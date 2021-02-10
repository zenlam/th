odoo.define('t_staff_planning.StaffPlanningRenderer', function (require) {
"use strict";

var AbstractRenderer = require('web.AbstractRenderer');
var core = require('web.core');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;

var StaffPlanningRenderer = AbstractRenderer.extend({
    tagName: 'div',
    className: 'o_staff_container',
    events: _.extend({}, AbstractRenderer.prototype.events, {
        'hover td': '_onTdHover',
    }),

    /**
     * @overide
     *
     * @param {Widget} parent
     * @param {Object} state
     * @param {Object} params
     */
    init: function (parent, state, params) {
        this._super.apply(this, arguments);
        this.$dataRender = {employees: {}, group: {}};
        // console.log(moment.tz("2014-06-01 12:00", "America/New_York"));
        // var offset = this.getSession().getTZOffset(moment());
        // var displayedValue = moment().add(offset, 'minutes');
        // this.compare = state.compare;
        // this.fieldWidgets = params.widgets || {};
        // this.timeRangeDescription = params.timeRangeDescription;
        // this.comparisonTimeRangeDescription = params.comparisonTimeRangeDescription;
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     * @param {Object} state
     * @param {Object} params
     */
    updateState: function (state, params) {
        // if (params.context !== undefined) {
        //     var timeRangeMenuData = params.context.timeRangeMenuData;
        //     if (timeRangeMenuData) {
        //         this.timeRangeDescription = timeRangeMenuData.timeRangeDescription;
        //         this.comparisonTimeRangeDescription = timeRangeMenuData.comparisonTimeRangeDescription;
        //     } else {
        //         this.timeRangeDescription = undefined;
        //         this.comparisonTimeRangeDescription = undefined;
        //     }
        // }
        // this.compare = state.compare;
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Used to determine whether or not to display the no content helper.
     *
     * @private
     * @returns {boolean}
     */
    _hasContent: function () {
    },
    /**
     * @override
     * @private
     * @returns {Deferred}
     */
    _render: function () {
        const {viewGroup} = this.state;
        this.$dataRender = {employees: {}, group: {}};
        let $container = $('<div>');
        this.renderHeader($container);
        this.renderRows($container);
        if (viewGroup === 'role') {
            this.renderFooter($container);
        }
        this.$el.html($container.contents());

        // this.expandToggle();
        return this._super.apply(this, arguments);
    },
    renderFooter: function ($container) {
        const {cost} = this.state.data;
        let $wFooter = $(`<div class="o_staff_footer">`)
        let data = [{name: 'labour_cost', label: 'Total Labour Cost', cost: cost.labor_cost},
                 {name: 'working_time', label: 'Total Working Time', cost: cost.working_hours},
                 {name: 'labour_cost', label: 'Total OT Hours', cost: cost.ot_hours}]
        data.map((d) => $wFooter.append($(`<div class="ftCon"><div class="wLabel">${d.label}</div><div class="wContent">${d.cost}</div></div>`)))
        $container.append($wFooter)
    },
    _getRowsDay: function (d) {
        let start = moment().format("DD MMMM YYYY");
        let _start = moment().format("DD MMMM YYYY");

        start = moment(start).add(this.state.day, 'days');
        start = start.add(this.state.week, 'weeks');
        start = start.add(this.state.month, 'months');
        _start = moment(_start).add(this.state.day, 'days');
        _start = _start.add(this.state.week, 'weeks');
        _start = _start.add(this.state.month, 'months');

        let sFormat = start.format("DD_MM_YYYY");
        let dFormat = start.format("YYYY-MM-DD HH:mm:ss");
        let $wItem = $(`<div class="w_item"></div>`);
        let $employee = {$el: $wItem, date: {}, obj: d};
        for (let i=0; i<=23; i++) {
            _start.set('hour', i);
            let $item = $(`<div class="r_item for_day" data-hour="${i}" data-date="${_start.format("YYYY-MM-DD HH:mm:ss")}"></div>`);
            $employee.date[`${sFormat}_${i}`] = $item;
            $employee.$el.append($item);
        }
        this.$dataRender.employees[d.id] = $employee;
    },
    _getRowsWeek: function (d) {
        let viewGroup = this.state.viewGroup;
        let _day = moment().add(this.state.day, 'days')
        // monday = moment(monday).add(this.state.day, 'days');
        _day.add(this.state.week, 'weeks')
        _day.add(this.state.month, 'months')
        // let monday = _day.startOf('week')

        let current = moment().format("DD_MM_YYYY");
        let monday = _day.startOf('week');
        // monday = moment(monday).add(this.state.viewData, 'weeks');
        let calDate = (d) => moment(monday).add(d, 'days').format("DD_MM_YYYY");
        let calData = (d) => moment(monday).add(d, 'days').format("YYYY-MM-DD HH:mm:ss");
        let calDisplay = (d) => moment(monday).add(d, 'days').format("dddd, Do");
        let weeks = [{label: calDisplay(0), name: 'sun', data: calData(0), date: calDate(0)}, {label: calDisplay(1), name: 'mon', data: calData(1), date: calDate(1)}, {label: calDisplay(2), name: 'tues', data: calData(2), date: calDate(2)},
                     {label: calDisplay(3), data: calData(3), date: calDate(3)}, {label: calDisplay(4), data: calData(4), date: calDate(4)}, {label: calDisplay(5), data: calData(5), date: calDate(5)}, {label: calDisplay(6), data: calData(6), date: calDate(6)}]
        let $wItem = $(`<div class="w_item"></div>`);

        let $employee = {$el: $wItem, date: {}, obj: d};
        weeks.map((d, i) => {
            let week = weeks[i];
            let $item = $(`<div class="r_item ${current === week.date ? 'current' : null}" data-date="${d.data}">
                                <div class="r_tran">
                                    <i class="i_add fa fa-plus-circle"></i>
                                </div>
                           </div>`)
            $employee.date[d.date] = $item;
            $employee.$el.append($item);
        });
        this.$dataRender.employees[d.id] = $employee;
    },
    _getRowsMonth: function (d) {
        let current = moment().format("DD_MM_YYYY");
        let _day = moment().add(this.state.day, 'days')
        // monday = moment(monday).add(this.state.day, 'days');
        _day.add(this.state.week, 'weeks')
        let dateOfMonth = _day.clone().add(this.state.month, 'months').endOf('month').date();
        let startMonth = _day.clone().add(this.state.month, 'months').startOf('month');
        let _startMonth = _day.clone().add(this.state.month, 'months').startOf('month');
        let $wItem = $(`<div class="w_item"></div>`);
        let $employee = {$el: $wItem, date: {}, obj: d};
        for (let i=1; i<=dateOfMonth; i++) {
            let curr = startMonth.add(1, 'days').format('DD_MM_YYYY');
            let data_date = _startMonth.add(1, 'days').format('YYYY-MM-DD HH:mm:ss');
            let $item = $(`<div class="r_item ${current === curr ? 'current' : null}" data-date="${data_date}">
                                <div class="r_tran">
                                    <i class="i_add fa fa-plus-circle"></i>
                                </div>
                           </div>`);
            $employee.date[curr] = $item;
            $employee.$el.append($item);
        }
        this.$dataRender.employees[d.id] = $employee;
    },
    _getHeaderDay: function (group=false) {
        let start = moment().format("DD MMMM YYYY");
        start = moment(start).add(this.state.week, 'weeks')
        start = start.add(this.state.month, 'months')
        start = start.add(this.state.day, 'days').format("DD MMMM YYYY");
        let $wItem = $(`<div class="w_item"></div>`);
        if (group) {
            for (let i=0; i<=23; i++) {
                $wItem.append($(`<div class="h_item"></div>`));
            }
        } else {
            for (let i = 0; i <= 23; i++) {
                $wItem.append($(`<div class="h_item"><label>${i} <span>${i > 12 ? "pm" : "am"}</span></label></div>`));
            }
        }
        return {displayHeader: start, $wItem: $wItem}
    },
    _getHeaderWeek: function (group=false) {
        // let monday = moment().startOf('week');
        let _day = moment().add(this.state.day, 'days')
        // monday = moment(monday).add(this.state.day, 'days');
        _day.add(this.state.week, 'weeks')
        _day.add(this.state.month, 'months')
        let monday = _day.startOf('week')
        // monday = moment(monday).add(this.state.month, 'months');
        // monday = moment(monday).add(this.state.viewData, 'weeks');

        let calDate = (d) => moment(monday).add(d, 'days').format("dddd, Do");
        let end = moment(monday).add(6, 'days').format("DD MMMM YYYY");
        let $wItem = $(`<div class="w_item"></div>`);
        let weeks = [{label: calDate(0), name: 'sun'}, {label: calDate(1), name: 'mon'}, {label: calDate(2), name: 'tues'},
                     {label: calDate(3)}, {label: calDate(4)}, {label: calDate(5)}, {label: calDate(6)}];
        if (group) {
            for (let i=0; i<weeks.length; i++) {
                $wItem.append($(`<div class="h_item"></div>`));
            }
        }else {
            for (let i = 0; i < weeks.length; i++) {
                $wItem.append($(`<div class="h_item"><label>${weeks[i].label}</label></div>`));
            }
        }
        return {displayHeader: `${monday.format("DD MMMM YYYY")} - ${end}`, $wItem: $wItem};
    },
    _getHeaderMonth: function (group=false) {
        // let current = moment();
        let current = moment().add(this.state.day, 'days')
        // monday = moment(monday).add(this.state.day, 'days');
        current.add(this.state.week, 'weeks')
        current = current.add(this.state.month, 'months');
        let $wItem = $(`<div class="w_item"></div>`);
        let dateOfMonth = current.endOf('month').date();
        if (group) {
            for (let i=1; i<=dateOfMonth; i++) {
                $wItem.append($(`<div class="h_item"></div>`));
            }
        } else {
            for (let i=1; i<=dateOfMonth; i++) {
                $wItem.append($(`<div class="h_item"><label>${i}</span></label></div>`));
            }
        }
        return {displayHeader: current.format("MMMM YYYY"), $wItem: $wItem};
    },
    renderGroup: function (employees) {
        let viewType = this.state.viewType;
        let _renderGroup = (name) => {
            let $wGroup = $(`<div class="w_group"><div class="w_header_group"></div><div class="w_body_group"></div></div>`);
            let $leftHeaderGroup = $(`<div class="r_l"><i class="fa fa-plus" style="font-size: 16px"></i><label class="lbl_group">${name}</label></div>`);
            let {$wItem} = eval(`this._getHeader${viewType.charAt(0).toUpperCase() + viewType.slice(1)}(true)`);
            $wGroup.find('.w_header_group').append($leftHeaderGroup);
            $wGroup.find('.w_header_group').append($wItem);
            return $wGroup;
        }
        let groups = {};
        if (!this.$dataRender.hasOwnProperty("group")) {
            this.$dataRender.group = {}
        }
        employees.map((d, i) => {
            if (!groups.hasOwnProperty(d.role_id)) {
                groups[d.role_id] = {name: d.role_name, employees: [], role_id: d.role_id};
            }
            groups[d.role_id].employees.push(d);
        });
        Object.keys(groups).map((d, i) => {
            d = groups[d];
            let group = {$el: _renderGroup(d.name), employees: d.employees};
            this.$dataRender.group[d.role_id] = group;
        });
    },
    renderHeader: function ($container) {
        let viewType = this.state.viewType;
        let {displayHeader, $wItem} = eval(`this._getHeader${viewType.charAt(0).toUpperCase() + viewType.slice(1)}()`);
        let $header = $('<div class="o_staff_header"><div class="o_staff_hl"></div><div class="o_staff_hr"></div></div>');
        let $day = $(`<div class="top"><label>${displayHeader}</label></div>`);
        let $wContainer = $('<div class="bot"><div class="r_l"></div></div>');
        $wContainer.append($wItem);
        $header.find('.o_staff_hr').append($day);
        $header.find('.o_staff_hr').append($wContainer);
        $container.append($header);
    },
    checkResizeFor: function (top, rs, bl=1) {
        let getTop = ($e) => parseFloat($e.css("top").replace("px", ""));
        let result = top;
        for (let i=0; i<rs.length; i++) {
            let currentRSTop = getTop($(rs[i]));
            if (top === currentRSTop) {
                if ($(rs[i]).attr("data-for")) {
                    result = this.checkResizeFor(top + 30*bl, rs);
                }
                break;
            }
        }
        return result;
    },
    resortResizable: function ($rs, top) {
        let self = this;
        let getTop = ($e) => parseFloat($e.css("top").replace("px", ""));
        let ov = $rs.filter((d, i) => getTop($($rs[d])) === top);
        if (ov.length > 0) {
            $rs.map((d, i) => {
                let currentRSTop = getTop($($rs[d]));
                if (currentRSTop >= top) {
                    $($rs[d]).css({top: self.checkResizeFor(currentRSTop+30, $rs)+"px"});
                }
            });
        }
    },
    renderResizeFor: function (employee, key, iCount, top, resize_key) {
        let self = this;
        let objKey = Object.keys(employee.date);
        let currIndex = objKey.indexOf(key);
        let _htmlResize = (data_for, top) => `<div class="resizable rs_for" data-id="rs_${Math.random()}" data-for="${data_for}" style="top: ${top}px"></div>`;
        for (let i = 1; i <= iCount; i++) {
            let _k = objKey[currIndex + i];
            if (_k) {
                let rs = employee.date[_k].find('.resizable');
                let getTop = ($e) => parseFloat($e.css("top").replace("px", ""));
                let ov = rs.filter((d, i) => getTop($(rs[d])) === top);
                if (ov.length > 0) {
                    self.resortResizable(rs, top);
                }
                employee.date[_k].append(_htmlResize(resize_key, top));
            }
        }
    },
    renderRows: function ($container) {
        let self = this;
        let viewType = this.state.viewType;
        let openShift = this.state.openShift;
        let myShift = this.state.myShift;
        let viewGroup = this.state.viewGroup;
        let $body = $('<div class="o_staff_body">');
        let employees = this.state.data['employee_data'].filter((d, i) => {
            return d.role_id
        });

        let data = this.state.data['staff_data'];
        console.log(data);
        // console.log(data);
        // data.sort((d) => d.start_date);
        let dateFormat = "YYYY-MM-DD HH:mm";
        let strToDate = (strDate) => moment(strDate, dateFormat);
        let itemWithDate = (employee_id, date) => {
            date = this.convertTimeZone(strToDate(date))
            // date = strToDate(date);
            let kI = null;
            if (viewType === 'day') {
                kI = date.format("DD_MM_YYYY_H");
            }else {
                kI = date.format("DD_MM_YYYY");
            }
            return kI;
        };
        if (viewGroup === "employee") {
            if (openShift) {
                employees.push({color: "#cdcdcd", id: 0, name: "Open Shift", role_id: 1, role_name: "Chef"});
            }
        }
        // _employee_data.append({'id': employee.id, 'name': employee.name, 'role_id': employee.role_id.id, 'role_name': employee.role_id.name,
        //                            'color': employee.role_id.colour, 'image_small': employee.image_small})
        let check_key = []
        if (viewGroup === "role") {
            employees = [];
            data.map((d, i) => {
                let key = `${d.employee_id[0]}_${d.role_id[0]}`;
                if (check_key.indexOf(key) < 0 && d.role_id) {
                    check_key.push(key);
                    employees.push({
                        'id': key, 'name': d.employee_id[1], 'role_id': d.role_id[0],
                        'role_name': d.role_id[1], 'color': d.colour, image_small: d.image_small
                    })
                }
            });
        }
        employees.map((d, i) => {
            eval(`this._getRows${viewType.charAt(0).toUpperCase() + viewType.slice(1)}(d)`);
        });
        data.map((d, i) => {
            let dKey = itemWithDate(d.id, d.start_date);
            let kEmployee = 0;
            if (viewGroup === "role") {
                kEmployee = `${d.employee_id[0]}_${d.role_id[0]}`
            }else if (d.employee_id) {
                kEmployee = d.employee_id[0];
            }

            let employee = this.$dataRender.employees[kEmployee];
            if (employee) {
                let $item = employee.date[dKey];
                if ($item) {
                    let typeF = viewType === 'day' ? 'hours' : 'days';
                    let timeData = strToDate(d.end_date).diff(strToDate(d.start_date), typeF);
                    let half = 0;
                    if (viewType === 'day') {
                        half = strToDate(d.start_date).minutes();
                        if (timeData === 0) {
                            timeData = 1;
                        }
                    } else {
                        timeData += 1;
                    }
                    let {top, id} = this.renderResizable($item, timeData, half, d, employee);
                    if (timeData > 1) {
                        timeData -= 1;
                        self.renderResizeFor(employee, dKey, timeData, top, id);
                    }
                }
            }
        });
        if (viewGroup === "role") {
            this.renderGroup(employees);
            Object.keys(this.$dataRender.group).map((d, i) => {
                d = this.$dataRender.group[d];
                d.employees.map((e, idx) => {
                    let $employee = this.$dataRender.employees[e.id];
                    let $wContainer = $(`<div class="w_container ${$employee.obj.color}">
                                    <div class="r_l" employee_id="${$employee.obj.id}" role_id="${$employee.obj.role_id}">
                                        <div class="w_image"><img src="data:image/gif;base64,${$employee.obj['image_small']}" /></div>
                                        <label>${$employee.obj.name}</label>
                                    </div>
                                 </div>`);
                    $wContainer.append($employee.$el);
                    d.$el.find('.w_body_group').append($wContainer);
                });
                $body.append(d.$el);
            });
            $container.append($body);
            this.calGroup($container);
        }else {
            Object.keys(this.$dataRender.employees).map((d, i) => {
                let $employee = this.$dataRender.employees[d];
                if ($employee) {
                    let $wContainer = $(`<div class="w_container ${$employee.obj.color}">
                                    <div class="r_l" employee_id="${$employee.obj.id}" role_id="${$employee.obj.role_id}">
                                    ${$employee.obj['image_small'] ? 
                                        `<div class="w_image"><img src="data:image/gif;base64,${$employee.obj['image_small']}" /></div>` : ""}
                                        <label>${$employee.obj.name}</label>
                                    </div>
                                 </div>`)
                    $wContainer.append($employee.$el);
                    $body.append($wContainer);
                }
            });
            $container.append($body);
        }
    },
    getTop: function ($rs) {
        return parseFloat($rs.css("top").replace("px", ""));
    },
    strToDate: function (strDate) {
        let dateFormat = "YYYY-MM-DD HH:mm";
        return moment(strDate, dateFormat);
    },
    convertHex: function(hex,opacity){
        hex = hex.replace('#','');
        let r = parseInt(hex.substring(0,2), 16);
        let g = parseInt(hex.substring(2,4), 16);
        let b = parseInt(hex.substring(4,6), 16);

        let result = 'rgba('+r+','+g+','+b+','+opacity/100+')';
        return result;
    },
    renderResizable: function ($item, iCount=1, half=0, data, employee) {
        let itemWidth = $item[0].getBoundingClientRect().width;
        let top = 0;
        let resizable = $item.find(".resizable");
        let tops = [];
        let color = data.colour;
        resizable.map((d, i) => {
            let $rs = $(resizable[d]);
            let offsetLeft = $rs.offset().left;
            if (!(offsetLeft >= ($item.offset().left + (itemWidth || 1)))) {
                tops.push(this.getTop($rs));
            }
        });
        tops.sort();
        while (tops.includes(top)) {
            top += 30;
        }
        let dOrL = this.lightOrDark(color);
        let rsId = `rs_${Math.random()}`;
        let $rs = $(`<div class="resizable" data-data="${data.id}" data-id="${rsId}" style="background-image: repeating-linear-gradient(-45deg, ${color} 0 10px, ${this.convertHex(color, 80)} 10px 20px); left: ${half > 0 ? 50 : 0}%; width: calc(${100*iCount+(half > 0 ? 50 : 0)}% + ${iCount*1}px); top: ${top}px">
                        <span class="o_start"></span>
                        <div class="resizers">
                            <div class="i_drag">
                                <div class="o_content"><label style="color: ${dOrL === "dark" ? "white" : "#323258"}" class="txt_truncate"></label></div>
                            </div>
                            <div class="resizer left"><div></div></div>
                            <div class="resizer right"></div>
                        </div>
                     </div>`);
        this.setDisplayTime($rs, data, employee);
        $item.append($rs);
        $item.css({minHeight: top+30+'px'});
        return {id: rsId, top: top};
    },
    _getHoursOfDay: function ($resizable) {
        let time = parseFloat($resizable.attr('time'));
        let hours = parseFloat($resizable.attr('hours'));
        let half = (_time) => _time%Math.floor(_time) > 0 ? '30' : '00';
        let ng = (_time) => Math.floor(_time);
        let start = hours > 12 ? `${ng(hours)}:${half(hours)} pm` : `${hours == 0.5 ? "00:30" : ng(hours)+":"+half(hours)} am`;
        let end = hours+time;
        end = end > 12 ? `${ng(end)}:${half(end)} pm` : `${ng(end)}:${half(end)} am`;
        $resizable.find('.o_content label').text(`${start} - ${end}`);
    },
    lightOrDark: function (color) {
        var r, g, b, hsp;
        if (color.match(/^rgb/)) {
            color = color.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+(?:\.\d+)?))?\)$/);
            r = color[1];
            g = color[2];
            b = color[3];
        } else {
            color = +("0x" + color.slice(1).replace(
            color.length < 5 && /./g, '$&$&'));
            r = color >> 16;
            g = color >> 8 & 255;
            b = color & 255;
        }
        hsp = Math.sqrt(
        0.299 * (r * r) +
        0.587 * (g * g) +
        0.114 * (b * b)
        );
        if (hsp>127.5) {
            return 'light';
        }
        else {
            return 'dark';
        }
    },
    calGroup: function ($container) {
        let $wGroup = $container.find(".w_group");
        $wGroup.map((d, i) => {
            let $el = $($wGroup[d]);
            let $bodyGroup = $el.find('.w_body_group');
            let $headerGroup = $el.find('.w_header_group');
            let $wContainer = $bodyGroup.find('.w_container');
            let gNumber = {}
            $wContainer.map((d, i) => {
                let items = $($wContainer[d]).find('.r_item');
                items.map((_d, i) => {
                    if (!gNumber.hasOwnProperty(_d)) {
                        gNumber[_d] = 0;
                    }
                    gNumber[_d] += $(items[_d]).find('.resizable').length;
                })
            });
            let match = false;
            let sIndex = null;
            let eIndex = null;
            let gNew = {};
            console.log(gNumber);
            Object.keys(gNumber).map((d, i) => {
                d = parseInt(d);
                if (gNumber[d] > 0) {
                    if (gNumber[d] === gNumber[d + 1]) {
                        if (!match) {
                            sIndex = d;
                            gNew[d] = {index: d, label: gNumber[d], count: 1};
                        }
                        gNew[sIndex].count += 1;
                        match = true;
                        eIndex = d + 1;
                    } else if (d != eIndex) {
                        gNew[d] = {index: d, label: gNumber[d], count: 1}
                        match = false;
                    } else {
                        match = false;
                    }
                }
            });
            let hItems = $headerGroup.find('.h_item');
            Object.keys(gNew).map((d, i) => {
                let gItem = gNew[d];
                let $item = $(hItems[gItem.index]);
                let wItem = $item[0].getBoundingClientRect().width;
                $item.append(`<div class="wh_label" style="width: calc(${100*gItem.count}% - 2px)"><div class="h_line"><span class="span_l"></span><span class="span_r"></span></div><div class="w_label"><label>${gItem.label}</label></div></div>`)
            });
        });
    },
    convertTimeZone: function (date) {
        var offset = this.getSession().getTZOffset(date);
        return date.clone().add(offset, 'minutes');
    },
    setDisplayTime: function ($resizable, d, employee) {
        let display = null;
        let viewType = this.state.viewType;
        let start_date = this.convertTimeZone(this.strToDate(d.start_date));
        let end_date = this.convertTimeZone(this.strToDate(d.end_date));
        // let start_date = this.strToDate(d.start_date);
        // let end_date = this.strToDate(d.end_date);
        if (viewType === 'day') {
            display = `${start_date.format("HH:mm A")} - ${end_date.format("HH:mm A")} ${employee.obj['role_name']}`
        }else {
            let diff = end_date.diff(start_date, "days")
            if (diff > 0) {
               display = `${start_date.format("YYYY-MM-DD")} - ${end_date.format("YYYY-MM-DD")} ${employee.obj['role_name']}`
            } else {
               display = `${start_date.format("HH:mm A")} - ${end_date.format("HH:mm A")} ${employee.obj['role_name']}`
            }
        }
        $resizable.find('.o_content label').text(display);
    },
});

return StaffPlanningRenderer;
});
