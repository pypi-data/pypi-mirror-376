import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the jupyterlab_theme_python_courses extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_theme_python_courses:plugin',
  description: 'A JupyterLab extension.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jupyterlab_theme_python_courses is activated!');
  }
};

export default plugin;
