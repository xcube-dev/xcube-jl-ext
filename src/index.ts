import { ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin } from "@jupyterlab/application";
import { PageConfig } from '@jupyterlab/coreutils';
import { ILauncher } from "@jupyterlab/launcher";
import { ISettingRegistry } from "@jupyterlab/settingregistry";
import { ServerConnection } from '@jupyterlab/services';
import { ICommandPalette, MainAreaWidget, WidgetTracker } from "@jupyterlab/apputils";
import { Widget } from "@lumino/widgets";
import { requestAPI } from './handler';


async function activate(
    app: JupyterFrontEnd,
    settingRegistry: ISettingRegistry | null,
    palette: ICommandPalette | null,
    launcher: ILauncher | null,
    restorer: ILayoutRestorer | null
) {
    console.debug("Activating JupyterLab extension xcube-jl-ext:");
    console.debug("  ISettingRegistry:", settingRegistry);
    console.debug("  ICommandPalette:", palette);
    console.debug("  ILauncher:", launcher);
    console.debug("  ILayoutRestorer:", restorer);
    console.debug("  baseUrl:", PageConfig.getBaseUrl());
    console.debug("  wsUrl:", PageConfig.getWsUrl());
    console.debug("  shareUrl:", PageConfig.getShareUrl());
    console.debug("  treeUrl:", PageConfig.getTreeUrl());

    const settings = ServerConnection.makeSettings();
    console.debug("  serverSettings:", settings);

    let hasServerProxy: boolean | undefined;

    const request = {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            lab_url: settings.baseUrl
        })
    };

    requestAPI<any>('labinfo', request, settings)
        .then(labInfo => {
            console.log(labInfo);
            hasServerProxy = labInfo.has_proxy;
        })
        .catch(reason => {
            console.error(
                `xcube_jl_ext server extension problem:\n${reason}`
            );
        });

    if (settingRegistry !== null) {
        settingRegistry
            .load(plugin.id)
            .then(settings => {
                console.debug(
                    "xcube-jl-ext settings loaded:",
                    settings.composite
                );
            })
            .catch(reason => {
                console.error(
                    "Failed to load settings for xcube-jl-ext.",
                    reason
                );
            });
    }

    const getLocalServerUrl = async (): Promise<string> => {
        const serverState = await requestAPI<any>('server', {method: "PUT"}, settings);
        console.debug("xcube-jl-ext server state:", serverState);
        const port = serverState.port;
        const serverUrl = hasServerProxy
            ? `${settings.baseUrl}proxy/${port}`
            : `http://127.0.0.1:${port}`;
        let error;
        for (let i = 0; i < 100; i++) {
            try {
                const response = await fetch(serverUrl, {});
                if (response.ok) {
                    return serverUrl;
                }
                error = response.statusText;
            } catch (e) {
                error = e;
                console.error(e);
            }
        }
        throw new Error(error);
    }

    let widget: MainAreaWidget | null = null;
    let tracker: WidgetTracker<MainAreaWidget> | null = null;

    // Add an application command
    const commandID = "xcube:openViewer";

    app.commands.addCommand(commandID, {
        label: "xcube Viewer",
        iconClass: (args: any) => (args["isPalette"] ? "" : "xcube-icon"),
        execute: async () => {
            if (widget === null || widget.isDisposed) {
                console.debug("Creating new JupyterLab widget xcube-jl-ext");

                const serverUrl = await getLocalServerUrl();

                // Create a blank content widget inside of a MainAreaWidget
                const content = new Widget();
                const iframe = document.createElement('iframe');
                iframe.style.position = "absolute";
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                // iframe.src = "https://viewer.earthsystemdatalab.net/";
                iframe.src = `${serverUrl}/viewer/?serverUrl=${serverUrl}`
                    + "&serverName=xcube+JupyterLab+Integration"
                    + "&serverId=jupyterlab";
                content.node.appendChild(iframe);

                widget = new MainAreaWidget({content});
                widget.id = "xcube-viewer";
                widget.title.label = "xcube Viewer";
                widget.title.closable = true;
            }
            if (tracker !== null && !tracker.has(widget)) {
                // Track the state of the widget for later restoration
                tracker.add(widget).then(() => {
                    console.debug('JupyterLab widget xcube-jl-ext stored!');
                });
            }
            if (!widget.isAttached) {
                // Attach the widget to the main work area if it's not there
                app.shell.add(widget, "main");
            }
            // Activate the widget
            app.shell.activateById(widget.id);
        }
    });

    if (palette !== null) {
        // Add the command to the palette.
        palette.addItem({
            command: commandID,
            category: "Other"
        });
    }

    if (launcher !== null) {
        // Add the command to the launcher.
        launcher.add({
            command: commandID,
            category: "Other",
            rank: 0
        });
    }

    if (restorer !== null) {
        // Track and restore the widget state
        tracker = new WidgetTracker<MainAreaWidget>({
            namespace: "xcube"
        });
        restorer.restore(tracker, {
            command: commandID,
            name: () => "xcube"
        }).then(() => {
            console.debug('JupyterLab widget xcube-jl-ext restored!');
        });
    }

    console.log('JupyterLab extension xcube-jl-ext is activated!');
}

/**
 * Initialization data for the xcube-viewer-jl-ext extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
    id: "xcube-jl-ext:plugin",
    autoStart: true,
    optional: [
        ISettingRegistry,
        ICommandPalette,
        ILauncher,
        ILayoutRestorer
    ],
    activate
};

export default plugin;
