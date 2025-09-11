import logging
import uuid
import json
import asyncio
import requests

from sdk.ws import websocketWrapper
from sdk.version import sdk_version, sdk_type, sdk_it, sdk_email, sdk_code

class WebexCompassClient:
    def __init__(self, host_address,client_id='',client_secret='',auth_token='',additional_credentials={}):
        self.sesssion_id = str(uuid.uuid4())
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_token = auth_token
        self.additional_credentials = additional_credentials
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

        websocket_url = host_address
        compass_url = host_address
        if host_address in ["triage.qa.webex.com","triage.qa.webex.com/dev"]:
            websocket_url = f'wss://{host_address}/ws'
            compass_url = f'https://{host_address}'
        else:
            server_parts = host_address.split(":")
            if len(server_parts) == 2:
                server = server_parts[0]
                web_port = int(server_parts[1])
            else:
                server = server_parts[0]
                web_port = int("9000")
            
            websocket_port = int(web_port) + 1
            websocket_url = f'ws://{server}:{websocket_port}/ws'
            compass_url = f'http://{server}:{web_port}'

        #wss://triage.qa.webex.com/ws/0f4cee3d-c48c-48ce-b036-93e14b394408?client_id=e8af9516-c502-42a4-a211-40b7b3b7a50d&client_secret=e8af9516-c502-42a4-a211-40b7b3b7a50d&client_type=web_client&user_email=qiujin@cisco.com&user_code=111&it=compass-web&sdk_version=44.3.0
        self.websocket_uri = f"{websocket_url}/{self.sesssion_id}?client_id={self.client_id}&client_secret={self.client_secret}&client_type={sdk_type}&user_email={sdk_email}&user_code={sdk_code}&it={sdk_it}&sdk_version={sdk_version}&enable_chat_history=false"
        self.upload_uri = f"{compass_url}/upload/"

        self.websocket_connection = None
        self.started = False
        self.login_status = True
        self.ready = asyncio.Future()
        self.websocket : websocketWrapper = websocketWrapper()
        self.pending_messages = {}

    async def start(self, on_ready=None,on_broken=None):
        if self.client_id == '' or self.client_secret == '':
            raise Exception("client_id and client_secret are required")

        if self.login_status == False:
            raise Exception("Not logged in")
        if self.started == True:
            raise Exception("Already started")
        await self._do_start(on_ready=on_ready,on_broken=on_broken)
       
    async def stop(self):
        logging.info(f"stop")
        if self.websocket_connection:
            await self.websocket.disconnect()
        self.websocket_connection  = None
        self.started = False
        

    async def logout(self):
        pass

    '''
    Do fast anomaly check for logs file
    - download_link_or_local_file: 
          download link of the log file, jira link or controlhub link
    - local_file: local file path of the log file
            local file is expected to current_log.txt or last_run_current_log.txt
            zip file
    '''
    async def generate_anomaly_report(self,download_link_or_local_file, topics = []):
        if download_link_or_local_file.startswith("http"):
            return await self._generate_anomaly_report_from_url(download_link_or_local_file,topics)
        else:
            return await self._generate_anomaly_report_from_local_file(download_link_or_local_file,topics)
    
    # Do deep anomaly check for given domain
    # - log_hash: hash of the log file
    # - topic: domain of the log file
    # - log_file: log file name returned by generate_anomaly_report
    async def generate_anomaly_deep_analysis_report(self,log_hash,topic,log_file):
        msg = {
            "target": "webex_agent",
            "instruction": "anomaly-deep-analysis",
            "log-hash": log_hash,
            "topic": topic,
            "log-file": log_file,
            "report-name": "anomaly-deep-analysis",
            "report-format": "json"
        }
        report = await self._send_command(msg)
        report = json.loads(report["content"])
        return report

    async def llm_summary(self, llm_model_name, message, system_message):
        msg = {
            "target": "llm_agent",
            "instruction": "llm-summary",
            "llm-model-name": llm_model_name,
            "content": message,
            "system-message": system_message,
            "report-name": "llm-summary-report",
            "report-format": "json"
        }
        report = await self._send_command(msg)
        report = json.loads(report["content"])
        return report
    
    async def call_mcp_router(self, content : str):
        msg = {
            "target": "mcp_router_agent",
            "instruction": "mcp-tool-call",
            "content": content,
            "additional-credentials": self.additional_credentials,
        }

        report = await self._send_command(msg)
        return report["content"]

    # Do fast anomaly check for all supported domains
    # - download_link: download link of the log file, jira link or controlhub link
    async def _generate_anomaly_report_from_url(self,download_link, topics = []):
        msg = {
            "target": "webex_agent",
            "instruction": "anomaly-check-chat",
            "download-link": download_link,
            "report-name": "anomaly-check",
            "topic": ','.join(topics)
        }
        report = await self._send_command(msg)
        try:
            # report = json.loads(report["content"])
            pass
        except Exception as e:
            logging.error(f"Error when parsing anomaly report: {e}, download_link: {download_link}")
            logging.error(f"==>     report: {report}")
            report = None
        return report
    
    async def _generate_anomaly_report_from_local_file(self,local_file, topics = []):
        with open(local_file, 'rb') as file:
            files = {'file': (local_file, file)}

            message_id = str(uuid.uuid4())
            future = asyncio.Future()
            self.pending_messages[message_id] = future

            params = {'ws-session-id': self.sesssion_id,
                    'message-id': message_id,
                    "report-name": "anomaly-check",
                    "topic": ','.join(topics)}
            response = requests.post(self.upload_uri, files=files, data=params, verify=False)
            await future
            report = future.result()
            try:
                report = json.loads(report["content"])
            except Exception as e:
                logging.error(f"Error when parsing anomaly report: {e}, local_file: {local_file}")
                logging.error(f"==>     report: {report}")
                report = None
        return report

    async def _send_command(self, command):
        message_id = str(uuid.uuid4())
        command["message-id"] = message_id

        future = asyncio.Future()
        self.pending_messages[message_id] = future
        await self.websocket.send_message(json.dumps(command))
        await future
        received_message = future.result()
        return received_message
    
    async def _do_start(self,on_ready=None,on_broken=None):

        logging.info(f"_do_start to {self.websocket_uri}")
        def _on_ws_connected(websocket):
            self.websocket_connection = websocket
            self.started = True
            logging.debug(f"Connected to {self.websocket_uri}")
            if on_ready:
                on_ready()
            self.ready.set_result(True)

        def _on_ws_disconnected(websocket):
            self.websocket_connection = None
            self.started = False
            logging.debug(f"Disconnected to {self.websocket_uri}")
            if on_broken:
                on_broken()
            for future in self.pending_messages.values():
                future.set_result(None)
            self.ready.set_result(False)
            

        def _on_ws_message(message):
            message = json.loads(message)
            if message['instruction'] == 'chat':
                command_id = message["message-id"]
                future = self.pending_messages.get(command_id)
                if future is None:
                    logging.debug(f"Received message without a pending message: {message}")
                    return
                self.pending_messages.pop(command_id)
                future.set_result(message)
            elif message['instruction'] == 'status':
                logging.info(f"Received status message: {message}")
            elif message['instruction'] == 'error':
                logging.error(f"Received error message: {message}")
                command_id = message["message-id"]
                future = self.pending_messages.get(command_id)
                if future is None:
                    logging.debug(f"Received error message without a pending message: {message}")
                    return
                self.pending_messages.pop(command_id)
                future.set_result(message)

        self.started = True
        await self.websocket.connect(self.websocket_uri, headers=self.headers, on_message=_on_ws_message, on_connected=_on_ws_connected, on_disconnected=_on_ws_disconnected)
