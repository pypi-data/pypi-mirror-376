/**
 * Initialization data for the jupyterlab_theme_python_courses extension.
 */
const plugin = {
    id: 'jupyterlab_theme_python_courses:plugin',
    description: 'A JupyterLab extension.',
    autoStart: true,
    activate: (app) => {
        console.log('JupyterLab extension jupyterlab_theme_python_courses is activated!');
    }
};
export default plugin;
