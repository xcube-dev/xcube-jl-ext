import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './handler';

/**
 * Initialization data for the xcube-jl-ext extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'xcube-jl-ext:plugin',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension xcube-jl-ext is activated!');

    requestAPI<any>('get_example')
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The xcube_jl_ext server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
