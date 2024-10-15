import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { callUntil, UnrecoverableError } from './util';

const API_NAMESPACE = 'xcube';

export interface LabInfo {
  lab_url: string;
  has_proxy?: boolean;
}

export interface ServerState {
  port: number;
  pid: number;
  status: string;
  cmdline: string[];
  name: string | null;
  username: string | null;
  returncode: number | null;
  stdout: string | null;
  stderr: string | null;
}

export interface ServerStatus {
  url: string;
  state: ServerState;
  response: any;
}

export function getViewerUrl(serverUrl: string) {
  return (
    `${serverUrl}/viewer/?serverUrl=${serverUrl}` +
    '&serverName=xcube+JupyterLab+Integration' +
    '&serverId=jupyterlab' +
    '&compact=1'
  );
}

/**
 * Set lab information.
 */
export async function setLabInfo(
  settings: ServerConnection.ISettings
): Promise<LabInfo> {
  const request = {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      lab_url: settings.baseUrl
    })
  };
  return callAPI<LabInfo>('labinfo', request, settings);
}

/**
 * Start xcube server and return, once it is ready to serve.
 */
export async function getServer(
  hasServerProxy: boolean,
  settings: ServerConnection.ISettings
): Promise<ServerStatus> {
  const serverState = await startServer(settings);
  assertServerStateOk(serverState);

  const serverPort = serverState.port;
  const serverUrl = hasServerProxy
    ? `${settings.baseUrl}proxy/${serverPort}`
    : `http://127.0.0.1:${serverPort}`;

  const fetchServerInfo = async (): Promise<any> => {
    const serverState = await getServerState();
    assertServerStateOk(serverState);
    const response = await fetch(serverUrl);
    if (!response.ok) {
      throw new ServerConnection.ResponseError(response);
    }
    return response.json();
  };

  const serverResponse = await callUntil(fetchServerInfo, 3000, 10);
  console.info('xcube server response:', serverResponse);

  return {
    url: serverUrl,
    state: serverState,
    response: serverResponse
  };
}

function assertServerStateOk(serverState: ServerState) {
  if (serverState.status === 'running' || serverState.status === 'sleeping') {
    return; // Ok!
  }
  console.debug('xcube-jl-ext server state:', serverState);
  let message =
    'xcube server could not be started or terminated unexpectedly. ';
  if (typeof serverState.stderr === 'string') {
    message += `Message: ${serverState.stderr}. `;
  }
  if (typeof serverState.returncode === 'number') {
    message += `Exit code ${serverState.returncode}. `;
  }
  if (typeof serverState.status === 'string') {
    message += `Status: ${serverState.status}. `;
  }
  if (Array.isArray(serverState.cmdline)) {
    message += `Command-line: "${serverState.cmdline.join(' ')}". `;
  }
  throw new UnrecoverableError(message);
}

/**
 * Start xcube server.
 */
async function startServer(
  settings?: ServerConnection.ISettings
): Promise<ServerState> {
  return callAPI<ServerState>('server', { method: 'PUT' }, settings);
}

/**
 * Get xcube server state.
 */
async function getServerState(
  settings?: ServerConnection.ISettings
): Promise<ServerState> {
  return callAPI<ServerState>('server', { method: 'GET' }, settings);
}

/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @param settings Server connection settings
 * @returns The response body interpreted as JSON
 */
export async function callAPI<T>(
  endPoint = '',
  init: RequestInit = {},
  settings?: ServerConnection.ISettings
): Promise<T> {
  settings = settings || ServerConnection.makeSettings();

  const requestUrl = URLExt.join(settings.baseUrl, API_NAMESPACE, endPoint);

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error);
  }

  let data: any = await response.text();
  if (data.length > 0) {
    try {
      data = JSON.parse(data);
    } catch (error) {
      console.warn('Not a JSON response body.', response);
    }
  }

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data.message || data);
  }

  return data;
}
