odoo.define('t_staff_planning.StaffPlanningView', function (require) {
"use strict";

/**
 * The Pivot View is a view that represents data in a 'pivot grid' form. It
 * aggregates data on 2 dimensions and displays the result, allows the user to
 * 'zoom in' data.
 */

var AbstractView = require('web.AbstractView');
var core = require('web.core');
var PivotModel = require('t_staff_planning.StaffPlanningModel');
var PivotController = require('t_staff_planning.StaffPlanningController');
var PivotRenderer = require('t_staff_planning.StaffPlanningRenderer');
var viewRegistry = require('web.view_registry');

var _t = core._t;
var _lt = core._lt;

var StaffPlanningView = AbstractView.extend({
    display_name: _lt('StaffPlanning'),
    icon: 'fa-table',
    config: {
        Model: PivotModel,
        Controller: PivotController,
        Renderer: PivotRenderer,
    },
    viewType: 'kanban',
    enableTimeRangeMenu: 'true',
    /**
     * @override
     * @param {Object} params
     */
    init: function (viewInfo, params) {
        var self = this;
        this._super.apply(this, arguments);
        this.controllerParams.viewInfo = viewInfo;
    },
});


viewRegistry.add('staff', StaffPlanningView);

return StaffPlanningView;

});
