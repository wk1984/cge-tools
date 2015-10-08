# -*- coding: utf-8 -*- #
from bokeh.embed import components
from bokeh.models import CustomJS, TapTool

from .charts import get_provincial_scenario_line_plot
from .maps import get_provincial_regional_map
from .scenarios import provinces
from .utils import get_js_array, env


def render():
    plot, province_map, region_map = _get()
    template = env.get_template('viz/co2_by_province.html')
    script, div = components(dict(plot=plot, province_map=province_map, region_map=region_map), wrap_plot_info=False)
    return template.render(plot_script=script, plot_div=div)


def _get():
    parameter = 'CO2_emi'
    plot, line_renderers, text_renderers = get_provincial_scenario_line_plot(
        parameter=parameter,
        y_ticks=[0, 450, 900],
        plot_width=600,
    )
    region_map, province_map, source = get_provincial_regional_map(parameter=parameter)

    prefixed_renderers = {}
    for province in provinces.keys():
        prefixed_renderers['line_%s' % province] = line_renderers[province]
        prefixed_renderers['text_%s' % province] = text_renderers[province]

    province_map = _add_province_callback(province_map, prefixed_renderers, source)
    region_map = _add_region_callback(region_map, prefixed_renderers, source)
    return (plot, province_map, region_map)


def _add_province_callback(province_map, prefixed_renderers, source):
    js_array = get_js_array(prefixed_renderers.keys())
    code = '''
        var renderers = %s,
            selected = cb_obj.get('selected'),
            highlight_indexes = selected['1d']['indices'],
            alpha = 0.2,
            glyph = null;
        if ( highlight_indexes.length == 0 ) {
            alpha = 0.8;
        }
        Bokeh.$.each(renderers, function(key, r) {
            glyph = r.get('glyph');
            glyph.set('line_alpha', alpha);
            glyph.set('text_alpha', alpha);
        });
        Bokeh.$.each(highlight_indexes, function(i, index) {
            var key = source.get('data')['index'][index];
            glyph = renderers['line_' + key].get('glyph');
            glyph.set('line_alpha', 0.8);
            glyph = renderers['text_' + key].get('glyph');
            glyph.set('text_alpha', 0.8);
        });
    ''' % js_array

    callback = CustomJS(code=code, args=prefixed_renderers)
    callback.args['source'] = source
    tap = province_map.select({'type': TapTool})
    tap.callback = callback
    return province_map

def _add_region_callback(region_map, prefixed_renderers, source):
    js_array = get_js_array(prefixed_renderers.keys())
    code = '''
        var renderers = %s,
            selected = cb_obj.get('selected')['1d']['indices'],
            selected_region = source.get('data')['region'][selected],
            regions = source.get('data')['region'],
            indices = [],
            idx = regions.indexOf(selected_region);
        while (idx != -1) {
            indices.push(idx);
            idx = regions.indexOf(selected_region, idx + 1);
        }
        cb_obj.get('selected')['1d']['indices'] = indices;
        source.trigger('change');
    ''' % js_array

    callback = CustomJS(code=code, args=prefixed_renderers)
    callback.args['source'] = source
    tap = region_map.select({'type': TapTool})
    tap.callback = callback
    return region_map
