odoo.define('t_staff_planning.field_time', function (require) {
"use strict";

/**
 * This module contains most of the basic (meaning: non relational) field
 * widgets. Field widgets are supposed to be used in views inheriting from
 * BasicView, so, they can work with the records obtained from a BasicModel.
 */

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var fieldRegistry = require('web.field_registry');



var FieldTime = AbstractField.extend({
    events: _.extend({}, AbstractField.prototype.events, {
        'focusout input': '_onFocus',
    }),
    init: function (parent, name, record, options) {
        this._super(parent, name, record, options);
        // this.selection = {day: {name: 'Day'}, week: {name: 'Week'}, month: {name: 'Month'}, year: {name: 'Year'}}
    },
    _setValue: function (value, options) {
        return this._super(value, options);
    },
    _doAction: function () {
        if (!this.isDestroyed()) {
            return this._setValue(this._getValue());
        }
    },
    _getValue: function () {
        return this.$el.find("input").val();
    },
    _render: function () {
        let $input = null;
        let data = this.value || "";
        if (this.mode == "edit") {
            $input = $(`<div>
                            <div class="w_input">
                                <input style="min-width: 100px" value="${data}" type="time" min="00:00:00" max="24:00:00" >
                            </div>
                        </div>`);
        }else {
            $input = `<span>${data}</span>`;
        }
        this.$el.html($input);
    },
    _onFocus: function (e) {
        this._doAction();
    },
    _onChange: function (e) {
        this._doAction();
    },
});

fieldRegistry.add("field_time", FieldTime);

return {
    FieldTime: FieldTime,
};
});
