# -*- coding: utf-8 -*- #
from bokeh.embed import components
from bokeh.models import TextInput, CustomJS

from .charts import get_national_scenario_line_plot
from .constants import scenarios
from .utils import get_js_array, env


def render():
    co2_plot, ap_plot, text = _get()
    template = env.get_template('viz/two_plots_with_selectors.html')
    script, div = components(dict(plot1=co2_plot, plot2=ap_plot, text=text), wrap_plot_info=False)
    return template.render(plot_script=script, plot_div=div, plot2_title="Population weighted PM2.5 exposure")


def _get():
    plot_width = 800
    he_plot, he_line_renderers = get_national_scenario_line_plot(
        parameter='PM25_exposure',
        y_ticks=[5000, 12000],
        plot_width=plot_width,
    )
    co2_plot, co2_line_renderers = get_national_scenario_line_plot(
        parameter='CO2_emi',
        y_ticks=[8000, 14000],
        plot_width=plot_width,
    )
    prefixed_line_renderers = {}
    for key in scenarios:
        prefixed_line_renderers['he_%s' % key] = he_line_renderers[key]
        prefixed_line_renderers['co2_%s' % key] = co2_line_renderers[key]

    line_array = get_js_array(prefixed_line_renderers.keys())
    code = '''
        var lines = %s,
            highlight = cb_obj.get('value').split(',');
        Bokeh.$.each(lines, function(key, line) {
            glyph = line.get('glyph');
            glyph.set('line_alpha', 0.1);
        });
        Bokeh.$.each(highlight, function(i, key) {
            function set_alpha(line) {
                glyph = line.get('glyph');
                glyph.set('line_alpha', 0.8);
            }
            set_alpha(lines['he_' + key]);
            set_alpha(lines['co2_' + key]);
        });
    ''' % line_array

    callback = CustomJS(code=code, args=prefixed_line_renderers)
    text = TextInput(callback=callback)
    return (co2_plot, he_plot, text)