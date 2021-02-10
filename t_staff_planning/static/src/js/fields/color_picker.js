odoo.define('web.t_staff_planning', function (require) {
"use strict";

/**
 * This module contains most of the basic (meaning: non relational) field
 * widgets. Field widgets are supposed to be used in views inheriting from
 * BasicView, so, they can work with the records obtained from a BasicModel.
 */

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var fieldRegistry = require('web.field_registry');
var ColorpickerDialog = require('web.colorpicker');


var FieldColor = AbstractField.extend({
    events: _.extend({}, AbstractField.prototype.events, {
        'click .color_picker': '_onClick'
    }),
    init: function (parent, name, record, options) {
        this._super(parent, name, record, options);
        this.state = {data: record.data[name] || 'green'}
    },
    _setValue: function (value, options) {
        if (this.field.trim) {
            value = value.trim();
        }
        this.setState({data: value})
        return this._super(value, options);
    },
    _doAction: function () {
        if (!this.isDestroyed()) {
            return this._setValue(this._getValue());
        }
    },
    _getValue: function () {
        return this.state.data;
    },
    _render: function () {
        this.$el.html(`<div class='color_picker' style="width: 40px; height: 30px; padding: 3px; border: 1px solid #cdcdcd"><div style="width: auto; height: 100%;; background-color: ${this.state.data}"></div></div>`);
    },
    setState: function (data) {
        Object.keys(data).map((d, i) => {
            this.state[d] = data[d];
            if (d == "data") {
                this.$el.find('.color_picker > div').css({backgroundColor: data[d]})
            }
        })
    },
    _onClick: function (event) {
        let self = this;
        var colorpicker = new ColorpickerDialog(this, {
            defaultColor: "#cdcdcd",
        });
        colorpicker.on('colorpicker:saved', this, function (ev) {
            ev.stopPropagation();
            self.setState({data: ev.data.cssColor});
            self._doAction();
        });
        colorpicker.open();
    },

});

fieldRegistry.add("field_color", FieldColor);

return {
    FieldColor: FieldColor,
};
});
