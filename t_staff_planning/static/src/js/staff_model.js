odoo.define('t_staff_planning.StaffPlanningModel', function (require) {
"use strict";

/**
 * Pivot Model
 *
 * The pivot model keeps an in-memory representation of the pivot table that is
 * displayed on the screen.  The exact layout of this representation is not so
 * simple, because a pivot table is at its core a 2-dimensional object, but
 * with a 'tree' component: some rows/cols can be expanded so we zoom into the
 * structure.
 *
 * However, we need to be able to manipulate the data in a somewhat efficient
 * way, and to transform it into a list of lines to be displayed by the renderer
 *
 * @todo add a full description/specification of the data layout
 */

var AbstractModel = require('web.AbstractModel');
var concurrency = require('web.concurrency');
var dataComparisonUtils = require('web.dataComparisonUtils');
var core = require('web.core');
var session = require('web.session');
var utils = require('web.utils');
var pyUtils = require('web.py_utils');
var Dialog = require('web.Dialog');
var view_dialogs = require('web.view_dialogs');

var _t = core._t;
var QWeb = core.qweb;
var FormViewDialog = view_dialogs.FormViewDialog;

var computeVariation = dataComparisonUtils.computeVariation;

var _t = core._t;

var StaffPlaningModel = AbstractModel.extend({
    /**
     * @override
     * @param {Object} params
     */
    init: function () {
        this._super.apply(this, arguments);
        this.numbering = {};
        this.data = null;
        this.viewType = 'week';
        this.viewData = 0;
        this.viewGroup = "employee";
        this.openShift = false;
        this.myShift = false;
        // this.group = false;
        this.expand = true;
        this.initDomain = this._init_domain();
        this._loadDataDropPrevious = new concurrency.DropPrevious();
    },
    /**
     * @override
     * @param {Object} [options]
     * @param {boolean} [options.raw=false]
     * @returns {Object}
     */
    setView: function (viewType) {
        this.viewType = viewType;
    },
    getView: function () {
        return this.viewType;
    },
    onWrite: function (res_id, data) {
        let self = this;
        let params = {
            model: "staff.planning",
            method: "write",
            args: [res_id, data]
        }
        return this._rpc(params);
    },
    onDelete: function (res_id) {
        let params = {
            model: "staff.planning",
            method: "unlink",
            args: [res_id]
        }
        return this._rpc(params);
    },
    copyPreviousWeek: function (data) {
        let self = this;
        return this._rpc({
                model: 'staff.planning',
                method: 'copy_previous_week',
                args: [data],
            }).then(function (result) {
                // self.viewGroup = "role";
            });
    },
    getDomain: function () {
        var searchData = this.getParent().searchView;
        let results = {};
        if (searchData) {
            var searchData = searchData.build_search_data();
            var userContext = this.getSession().user_context;
            results = pyUtils.eval_domains_and_contexts({
                domains: searchData.domains,
                contexts: [userContext].concat(searchData.contexts),
                group_by_seq: searchData.groupbys || []
            });
        }
        return results
    },
    onSearch: function (domain=[], domain_hr=[]) {
        let self = this;
        let data = this.getDomain();
        if (this.initDomain.length > 0) {
            domain = this.initDomain.concat(domain);
            this.initDomain = [];
        }
        if (data.hasOwnProperty("domain")) {
            domain = data.domain.concat(domain);
        }
        if (data.context) {
            if (data.context.hasOwnProperty("open_shift")) {
                this.openShift = data.context['open_shift'] === 1 ? true : false;
            }
            if (data.context.hasOwnProperty("my_shift")) {
                this.myShift = data.context['my_shift'] === 1 ? true : false;
            }
        }
        if (data.hasOwnProperty("group_by")) {
            if (data.group_by.includes("role_id")) {
                self.viewGroup = "role"
            }else if (!self.viewGroup) {
                self.viewGroup = "employee";
            }
        }
        let employee_id = location.hash.split("&").map((d, i) => d.split("=")).filter((d) => d[0] === "employee_id")
        if (employee_id.length > 0) {
            domain.push(['employee_id', '=', parseInt(employee_id[0][1])])
            domain_hr.push(['id', '=', parseInt(employee_id[0][1])])
        }
        return this._rpc({
                model: 'staff.planning',
                method: 'get_data',
                args: [domain, domain_hr],
            }).then(function (result) {
                self.data.data = result;
            });
    },
    onCreate: function (data) {
        let self = this;
        let params = {
            model: "staff.planning",
            method: "create",
            args: [data]
        }
        return this._rpc(params);
    },
    createSendSchedule: function (data) {
        let self = this;
        let params = {
            model: "planning.send",
            method: "create",
            args: [data]
        }
        return this._rpc(params);
    },
    onShowSendSchedule: function (res_id=false, func) {
        let {staff_data} = this.data.data;
        let employees = staff_data.map((d, i) => d.employee_id[0]);
        let labelDisplay = "Planning of 1 day";
        if (this.viewType === 'week') {
            labelDisplay = "Planning of 1 week";
        }else if (this.viewType === 'month') {
            labelDisplay = "Planning of 1 month";
        }
        let self = this;
            this._rpc({
                model: "planning.send",
                method: 'get_form_view_id',
                args: [],
            }).then(function (viewId) {
                self.do_action({
                    type:'ir.actions.act_window',
                    res_id: res_id,
                    readonly: false,
                    mode: "edit",
                    res_model: "planning.send",
                    views: [[viewId || false, 'form']],
                    target: 'new',
                    context: {employee_ids: employees, label_display: labelDisplay, host_url: location.href, host: location.host},
                }, func);
        });
    },
    onShowCreate: function (res_id=false, func=()=> {}, on_remove=(res_id)=> {}, ctx={}) {
        const {isManager} = this.data.data;
        let self = this;
        let options = {
            res_model: "staff.planning",
            res_id: res_id,
            context: ctx,
            title: "Planning Schedule",
            on_saved: (record) => {
                func(record);
            },
            on_remove: () => {
               on_remove(res_id);
               // self.onDelete(res_id)
            }
        };
        if (res_id && isManager) {
            options.deletable = true;
        }
        let dialog =  new FormViewDialog(this, options);
        // let _save = dialog._save.bind(dialog);
        // dialog._save = function () {
        //     alert('od');
        //     return _save();
        //     // var self = this;
        //     // return this.form_view.saveRecord(this.form_view.handle, {
        //     //     stayInEdit: true,
        //     //     reload: false,
        //     //     savePoint: this.shouldSaveLocally,
        //     //     viewType: 'form',
        //     // }).then(function (changedFields) {
        //     //     // record might have been changed by the save (e.g. if this was a new record, it has an
        //     //     // id now), so don't re-use the copy obtained before the save
        //     //     var record = self.form_view.model.get(self.form_view.handle);
        //     //     self.on_saved(record, !!changedFields.length);
        //     // });
        // };
        dialog.open()
    },
    // onShowCreate: function (res_id=false, func) {
    //     let self = this;
    //         this._rpc({
    //             model: "staff.planning",
    //             method: 'get_form_view_id',
    //             args: [],
    //         }).then(function (viewId) {
    //             self.do_action({
    //                 type:'ir.actions.act_window',
    //                 res_id: res_id,
    //                 readonly: false,
    //                 mode: "edit",
    //                 res_model: "staff.planning",
    //                 views: [[viewId || false, 'form']],
    //                 target: 'new',
    //                 context: {},
    //             }, func);
    //         });
    // },
    get: function (options) {
        return {
            data: this.data.data,
            viewType: this.viewType,
            viewData: this.viewData,
            day: this.day,
            week: this.week,
            month: this.month,
            viewGroup: this.viewGroup,
            expand: this.expand,
            openShift: this.openShift,
            myShift: this.myShift,
        };
    },
    load: function (params) {
        var self = this;
        this.data = {};
        return this.onSearch();
    },
    /**
     * @override
     * @param {any} handle this parameter is ignored
     * @param {Object} params
     * @returns {Deferred}
     */
    reload: function (params) {
        return this.onSearch();
    },
    // reload: function (handle, params) {
    //     var self = this;
    //     return this._loadData().then((d) => {
    //         alert(d)
    //     });
    // },
    convertTimeZone: function (date, add=true) {
        if (typeof date == 'string') {
            date = this.strToDate(date);
        }
        var offset = this.getSession().getTZOffset(date);
        if (add) {
            return date.clone().add(offset, 'minutes');
        }else {
            return date.clone().subtract(offset, 'minutes');
        }
    },
    _init_domain: function () {
        let strFormat = "YYYY-MM-DD HH:mm:ss",
            startDate = this.convertTimeZone(moment().startOf("week"), false).format(strFormat),
            endDate = this.convertTimeZone(moment().endOf("week"), false).format(strFormat);
        return ['|', '&', ['start_date', '<=', startDate], ['end_date', '>=', startDate],
                '&', '&', ['start_date', '>=', startDate], ['start_date', '<=', endDate],
                     '|', ['end_date', '<', endDate], ['end_date', '>', endDate], ['user_id', '=', this.getSession().uid]];
    },
    _loadData: function () {
        var searchData = this.getParent().searchView.build_search_data();
            var userContext = this.getSession().user_context;
            var results = pyUtils.eval_domains_and_contexts({
                domains: searchData.domains,
                contexts: [userContext].concat(searchData.contexts),
                group_by_seq: searchData.groupbys || []
            });
            console.log(results)
        return this.onSearch();
    },
});

return StaffPlaningModel;

});
