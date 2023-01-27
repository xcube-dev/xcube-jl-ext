import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { callUntil } from "./util";

const API_NAMESPACE = "xcube";

export interface LabInfo {
    lab_url: string;
    has_proxy?: boolean;
}

export interface ServerInfo {
    pid: number;
    port: number;
}

export interface ServerState extends ServerInfo {
    status: string;
    name: string;
    username: string;
    cmdline: string;
}

export interface ServerStatus {
    url: string;
    state: ServerState;
    response: any;
}

export function getViewerUrl(serverUrl: string) {
    return `${serverUrl}/viewer/?serverUrl=${serverUrl}`
        + "&serverName=xcube+JupyterLab+Integration"
        + "&serverId=jupyterlab"
        + "&compact=1";
}

/**
 * Set lab information.
 */
export async function setLabInfo(settings: ServerConnection.ISettings): Promise<LabInfo> {
    const request = {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            lab_url: settings.baseUrl
        })
    };
    return callAPI<LabInfo>('labinfo', request, settings);
}

/**
 * Start xcube Server and return, once it is ready to serve.
 */
export async function getServer(hasServerProxy: boolean,
                                settings: ServerConnection.ISettings): Promise<ServerStatus> {
    const serverState = await startServer(settings);
    console.debug("xcube-jl-ext server state:", serverState);
    if (serverState.status !== "running") {
        throw new Error(
            `xcube Server status is "${serverState.status}"`
            + ` for command line "${serverState.cmdline}".`
        );
    }

    const serverPort = serverState.port;
    const serverUrl = hasServerProxy
        ? `${settings.baseUrl}proxy/${serverPort}`
        : `http://127.0.0.1:${serverPort}`;

    const fetchServerInfo = async (): Promise<any> => {
        const response = await fetch(serverUrl);
        if (!response.ok) {
            throw new ServerConnection.ResponseError(response);
        }
        return response.json();
    }

    const serverResponse = await callUntil(fetchServerInfo, 5000, 10);
    console.info('xcube server response:', serverResponse);

    return {
        url: serverUrl,
        state: serverState,
        response: serverResponse,
    };
}


/**
 * Start xcube Server.
 */
async function startServer(settings?: ServerConnection.ISettings): Promise<ServerState> {
    const request = {
        method: "PUT"
    };
    return callAPI<ServerState>('server', request, settings);
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
