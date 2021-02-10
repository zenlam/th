odoo.define('t_staff_planning.StaffPlanningController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController');
var core = require('web.core');
var view_dialogs = require('web.view_dialogs');
var ColorpickerDialog = require('web.colorpicker');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');
var session = require('web.session');
var FieldMany2One = require('web.relational_fields').FieldMany2One;
var Widget = require('web.Widget');

var _t = core._t;
var QWeb = core.qweb;

var StaffPlanningController = AbstractController.extend({
    template: 'StaffPlanning',
    events: {
        'mousedown .resizer': 'onResize',
        'mousedown .i_drag': 'onDrag',
        // 'mouseover .r_item': 'onHover',
        'click .r_item.for_day': 'onCreateItem',
        'click .i_add': 'onCreateItem',
        'click .resizable': 'onShowItem',
        'mouseover .r_item': 'onShowIconCreate',
        'click .w_header_group': 'toggleGroup',
        'mouseover .resizable': 'showToolTip',
    },

    /**
     * @override
     * @param {Object} params
     * @param {Object} params.groupableFields a map from field name to field
     *   props
     * @param {boolean} params.enableLinking configure the pivot view to allow
     *   opening a list view by clicking on a cell with some data.
     */
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.mouseDown = false;
        this.mouseUp = false;
        this.stopMove = false;
        this.isClick = true;
        this.viewInfo = params.viewInfo;
        this.day = 0;
        this.week = 0;
        this.month = 0;
        this.iday = 0;
        this.outlet = null;
    },
    renderToolTip: function (data) {
        return $(`<div class="o_staff_tooltip" style="opacity: 0">
            <div class="tt-header"><span class="t_r"></span></div>
            <div class="tt-body">
                <ul>
                    <li>Start Date: <span class="os_tt_sdate">${data.start_date}</span></li>
                    <li>End Date: <span class="os_tt_edate">${data.end_date}</span></li>
                    <li>Allocated Hours: <span class="os_tt_ah">${data.allocated_hours}</span></li>
                </ul>
            </div>
            <div class="tt-footer"></div>
          </div>`);
    },
    hideToolTip: function () {
        $(document).find('.o_staff_tooltip').css({opacity: 0});
    },
    showToolTip: function (e) {
        let self = this;
        self.stopMove = false;
        let $resizable = $(e.currentTarget);
        const {outlet_manager_ids} = this.model.data.data;
        if (outlet_manager_ids.length > 0) {
            $resizable.parents('.r_item').find('.i_add').css({display: 'block'});
        }
        let run = true;
        let _renderToolTip = () => {
            if (!self.stopMove && run) {
                const {staff_data} = this.renderer.state.data;
                let getTop = ($e) => parseFloat($e.css("top").replace("px", ""));
                let data = staff_data.filter((d, i) => d.id == $resizable.attr("data-data"));
                if (data.length > 0) {
                    let $toolTip = $resizable.parents('body').find('.o_staff_tooltip');
                    if ($toolTip.length === 0) {
                        $toolTip = this.renderToolTip(data);
                        $(e.target).parents('body').append($toolTip);
                    }
                    data = data[0];
                    $toolTip.find(".os_tt_sdate").text(data.start_date);
                    $toolTip.find(".os_tt_edate").text(data.end_date);
                    $toolTip.find(".os_tt_ah").text(data.allocated_hours);
                    let l = $(e.currentTarget)[0].getBoundingClientRect().width / 2 + $(e.currentTarget).offset().left - $toolTip[0].getBoundingClientRect().width / 2;
                    $toolTip.css({top: $(e.currentTarget).offset().top + 45 + "px", left: l + "px"});
                    $toolTip.css({opacity: 1, zIndex: 1000});
                }
                e.stopPropagation();
            }
        }
        setTimeout(_renderToolTip, 2000);
        e.currentTarget.addEventListener('mouseout', (e) => {
            self.stopMove = true;
            run = false;
            let $resizable = $(e.currentTarget);
            $resizable.parents('.r_item').find('.i_add').css({display: 'none'});
            $resizable.parents('body').find('.o_staff_tooltip').css({opacity: 0, zIndex: -1});
            clearTimeout(_renderToolTip);
        }, true);
        e.stopPropagation();
    },
    onShowItem: function (event) {
        let self = this;
        if (self.isClick) {
            let $rs = $(event.currentTarget);
            let ctx = {
                outlet: self.outlet.lastSetValue ? self.outlet.lastSetValue.id : false,
            };
            this.model.onShowCreate(parseInt($rs.attr("data-data")),
                () => {
                    self.model._loadData().then((d) => {
                        self.update({data: self.model.data}, {reload: false});
                    });
                }, (res_id)=> {self.model.onDelete(res_id).then((d) => {
                    self.model._loadData().then((d) => {
                        self.update({data: self.model.data}, {reload: false});
                    });
            })}, ctx);
        }
        event.stopPropagation();
    },
    toggleGroup: function (event) {
        let $el = $(event.target);
        let $bodyGroup = $el.parents('.w_group').find('.w_body_group');
        let $headerGroup = $el.parents('.w_group').find('.w_header_group');
        let $icon = $headerGroup.find('i');
        if ($icon.hasClass('fa-plus')) {
            $icon.addClass("fa-minus");
            $icon.removeClass("fa-plus");
        }else {
            $icon.addClass("fa-plus");
            $icon.removeClass("fa-minus");
        }
        $headerGroup.find('i').addClass($bodyGroup.css("display") === "block" ? "fa-minus" : "fa-plus");
        $bodyGroup.css({display: $bodyGroup.css("display") === "block" ? "none" : "block"});
    },
    calGroup: function (event) {
        let $el = $(event.target);
        let $bodyGroup = $el.parents('.w_group').find('.w_body_group');
        let $headerGroup = $el.parents('.w_group').find('.w_header_group');
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
        let hItems = $headerGroup.find('.r_item');
        Object.keys(gNew).map((d, i) => {
            let gItem = gNew[d];
            let $item = $(hItems[gItem.index]);
            let wItem = $item[0].getBoundingClientRect().width;
            $item.append(`<div class="wh_label" style="width: ${wItem*gItem.count-2}px"><div class="h_line"><span class="span_l"></span><span class="span_r"></span></div><div class="w_label"><label>${gItem.label}</label></div></div>`)
        });
    },
    onShowIconCreate: function (event) {
        const {outlet_manager_ids} = this.model.data.data;
        if (outlet_manager_ids.length > 0) {
            let items = $(event.target).parents(".w_container").find(".r_item");
            items.each((index) => {
                let $el = $(items[index]);
                let osLeft = $el.offset().left;
                let wItem = $el[0].getBoundingClientRect().width;
                if (event.pageX >= osLeft && event.pageX <= (osLeft + wItem)) {
                    $el.find('.i_add').css({display: 'inline-block'});
                    $(event.target).mouseout((e) => {
                        $el.find('.i_add').css({display: 'none'});
                    });
                    return false;
                }
            });
        }
        event.stopPropagation();
    },
    getCssTop: function ($rs) {
        return parseFloat($rs.css("top").replace("px", ""));
    },
    convertTimeZone: function (date, add=true) {
        var offset = this.getSession().getTZOffset(date);
        if (add) {
            return date.clone().add(offset, 'minutes');
        }else {
            return date.clone().subtract(offset, 'minutes');
        }
    },
    getChecked: function (employee_id) {
        const {staff_data} = this.model.data.data;
        return staff_data.filter((d) => d.checked && d.employee_id && d.employee_id[0] == employee_id).length
    },
    onCreateItem: function (event) {
        let self = this;
        const {isManager, staff_data} = this.model.data.data;
        if (isManager) {
            let $item = $(event.target);

            if ($item.hasClass('i_add')) {
                $item = $item.parents(".r_item");
            }
            let $wContainer = $(event.target).parents('.w_container');
            let employee_id = $wContainer.find('.r_l').attr("employee_id");
            let role_id = $wContainer.find('.r_l').attr("role_id");
            let currentDate = moment($item.attr("data-date"), "YYYY-MM-DD HH:mm:ss")
            let startDate = currentDate.clone().subtract(this.getSession().getTZOffset(currentDate), "minutes").format("YYYY-MM-DD HH:mm:ss")
            let endDate = currentDate.clone().subtract(this.getSession().getTZOffset(currentDate), "minutes").add(this.model.viewType === 'day' ? 1 : 0, "hours").format("YYYY-MM-DD HH:mm:ss")

            let ctx = {
                default_start_date: startDate,
                default_end_date: endDate,
                default_employee_id: parseInt(employee_id),
                outlet: self.outlet.lastSetValue ? self.outlet.lastSetValue.id : false,
            };
            let show = false;
            this.model.onShowCreate(false,
                (record) => {
                    let sd_working_time = record.data.sd_working_time;
                    let allocated_hours = record.data.allocated_hours;
                    let employee_id = record.data.employee_id.res_id;
                    if (allocated_hours > sd_working_time && employee_id && self.getChecked(employee_id) === 0) {
                        show = true;
                        alert('This exceeds the standard working time allocated for this employee so this shift will be considered as an OT');
                    }
                    if (show) {
                        self.model.onWrite(record.data.id, {checked: true}).then((d) => {
                            self.reloadData();
                        })
                    }else {
                        self.reloadData();
                    }
                }, (res_id) => {
            }, ctx);
        }
        event.stopPropagation();
    },
    reloadData: function () {
        let self = this;
        self.model._loadData().then((d) => {
            self.update({data: self.model.data}, {reload: false});
        });
    },
    onAdd: function (event) {
        if (this.mouseDown) {
            this.mouseDown = false;
        }else {
            let $item = $(event.target);
            let itemWidth = $item[0].getBoundingClientRect().width;
            $item.append($(`<div class="resizable" data-id="rs_${Math.random()}" style="width: ${itemWidth}px">
                                <span class="o_start"></span>
                                <div class="resizers">
                                    <div class="i_drag">
                                        <div class="o_content"><label></label></div>
                                    </div>
                                    <div class="resizer left"><div></div></div>
                                    <div class="resizer right"></div>
                                </div>
                            </div>`));
            let viewType = this.model.getView();
            if (viewType === 'day') {
                $item.find('.resizable').attr({time: 1, hours: $item.attr('data-hour')});
            }else if (viewType === 'week') {
                $item.find('.resizable').attr({time: 23.59, day: $item.attr('data-day')});
            }else if (viewType === 'month') {
                $item.find('.resizable').attr({time: 1, month: $item.attr('data-month')});
            }
            this.setDisplayTime($item.find('.resizable'));
            event.stopPropagation();
        }
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
    _getHoursOfWeek: function ($resizable) {
        // let
    },
    _getHoursOfMonth: function ($resizable) {

    },
    setDisplayTime: function ($resizable) {
        let viewType = this.model.getView();
        if (viewType === "day") {
            this._getHoursOfDay($resizable);
        }else if (viewType === "week") {
            this._getHoursOfWeek();
        }else if (viewType === "month") {
            this._getHoursOfMonth();
        }
    },
    onDrag: function (event) {
        event.preventDefault();
        const {isManager} = this.model.data.data;
        if (isManager) {
            this.stopMove = true;
            this.mouseDown = true;
            this.isClick = true;
            this.hideToolTip();
            let self = this;
            var $target = $(event.target);
            let $resizable = $target.parents('.resizable');
            let cursorX = event.pageX - parseFloat($resizable.css("left").replace("px", ""));
            let OsTop = event.pageY - $resizable.offset().top;
            let wLeft = $target.parents('.w_container').find('.r_l')[0].getBoundingClientRect().width;
            let getLine = (top) => {
                let $w_container = $(document).find('.o_staff_body .w_container');
                let result = {};
                for (let i = 0; i < $w_container.length; i++) {
                    let $con = $($w_container[i]);
                    let osTop = $con.offset().top;
                    if ((top >= (osTop - 15) && ((top + 30) <= osTop + $con.height() + 15))) {
                        let _data = $con.find('.r_l').attr("employee_id").split("_")
                        result['employee_id'] = parseFloat(_data[0]);
                        if (_data.length > 1) {
                            result['role_id'] = parseFloat(_data[1]);
                        }
                        break;
                    }
                }
                return result;
            }

            let dragMove = (e) => {
                self.stopMove = true;
                self.isClick = false;
                let $tg = $(e.target);
                if ($tg.offset().left >= wLeft) {
                    $resizable.css({left: (e.pageX - cursorX) + "px", zIndex: 3000});
                }
                // let $hr = $tg.parents('.o_staff').find('.o_staff_hr');
                // if (($hr.offset().top + $hr[0].getBoundingClientRect().height) <= e.pageY) {
                $resizable.offset({top: e.pageY - OsTop});
                // }
                e.stopPropagation();
            };
            // $resizable[0].addEventListener('mousemove', dragMove, true);
            window.addEventListener('mousemove', dragMove, true);
            let dropDone = (e) => {
                let pLeft = e.pageX - cursorX;
                let absPLeft = Math.abs(pLeft);
                let $resizable = $target.parents('.resizable');
                let wHour = $resizable.parent()[0].getBoundingClientRect().width;
                let wLeft = $target.parents('.w_container').find('.r_l')[0].getBoundingClientRect().width;
                let hours = 0;

                let wResize = $resizable[0].getBoundingClientRect().width;
                let time = Math.floor(wResize / wHour);
                if (wResize % wHour > wHour) {
                    time += 1;
                }
                if (absPLeft % wHour > wHour / 1.5) {
                    absPLeft = (Math.floor(absPLeft / wHour) + 1) * wHour * (pLeft / absPLeft);
                    hours = Math.floor(($resizable.offset().left - wLeft) / wHour) + (pLeft >= 0 ? 1 : 0);
                } else if (absPLeft % wHour > (wHour / 2) / 2) {
                    absPLeft = ((Math.floor(absPLeft / wHour) * wHour) + wHour / 2) * (pLeft / absPLeft);
                    hours = Math.floor(($resizable.offset().left - wLeft) / wHour) + 0.5;
                } else {
                    absPLeft = Math.floor(absPLeft / wHour) * wHour * (pLeft / absPLeft);
                    hours = Math.floor(($resizable.offset().left - wLeft) / wHour) + (pLeft < 0 ? 1 : 0);
                }

                let dataUpdate = self.getData($resizable, hours, time);
                if (!self.isClick) {
                    let employee_update = getLine(e.pageY - OsTop);
                    if (Object.keys(employee_update).length > 0) {
                        dataUpdate.values.employee_id = employee_update.employee_id;
                        if (employee_update.hasOwnProperty('role_id')) {
                            dataUpdate.values.role_id = employee_update.role_id;
                        }
                    }
                }
                self.updateData(dataUpdate);
                $resizable.css({left: absPLeft + "px", zIndex: 100});
                $resizable.attr({hours: hours, time: time});

                this.setDisplayTime($resizable);
                window.removeEventListener('mouseup', dropDone, true);
                window.removeEventListener('mousemove', dragMove, true);
                e.stopPropagation();
            }
            window.addEventListener('mouseup', dropDone, true);
        }
        event.stopPropagation();
    },
    resizeOver: function($resizable, $target, right=true) {
            let wHour = $resizable.parent()[0].getBoundingClientRect().width;
            let wResize = $resizable[0].getBoundingClientRect().width;
            let leftRs = parseFloat($resizable.css("left").replace("px", ""));
            let wDu = right ? wResize-wHour+leftRs : Math.abs(leftRs);
            let _htmlResize = (data_for, top) => `<div class="resizable rs_for" data-id="rs_${Math.random()}" data-for="${data_for}" style="top: ${top}"></div>`;
            let getTop = ($e) => parseFloat($e.css("top").replace("px", ""));
            let getLeft = ($e) => parseFloat($e.css("left").replace("px", ""));
            let getWidth = ($el) => $el[0].getBoundingClientRect().width;
            let resizeTop = getTop($resizable);
            let findRSFor = ($el) => $el.find(`.resizable[data-for='${$resizable.attr("data-id")}']`);
            let checkRs = (top, rs, bl=1) => {
                let result = top;
                for (let i=0; i<rs.length; i++) {
                    let currentRSTop = getTop($(rs[i]));
                    if (top === currentRSTop) {
                        if ($(rs[i]).attr("data-for")) {
                            result = checkRs(top + 30*bl, rs);
                        }
                        break;
                    }
                }
                return result;
            }
            let reOrder = ($el, add=true, ap=null) => {
                let rs = $el.find(".resizable").not(ap);
                let first = true;
                rs.map((d, i) => {
                    let currentRSTop = getTop($(rs[d]));
                    if (add) {
                        if (currentRSTop >= resizeTop) {
                            $(rs[d]).css({top: checkRs(currentRSTop+30, rs)+"px"});
                        }
                    }else {
                        if (currentRSTop > resizeTop) {
                            $(rs[d]).css({top: first ? resizeTop : (checkRs(currentRSTop, rs) - 30) + "px"});
                            first = false;
                        }
                    }
                });
            }
            if (!right && leftRs > 0) {
                let current = $target.parents(".r_item");
                let nItems = Math.floor(leftRs/wHour);
                for (let i=0; i<nItems; i++) {
                    if (i > 0) {
                        current = current.next();
                    }
                    findRSFor(current).remove();
                    reOrder(current, false);
                }
                if (leftRs%wHour >= wHour/1.5) {
                    if (nItems > 0) {
                        current = current.next();
                        let rsFor = findRSFor(current);
                        if (rsFor.length === 0) {
                            reOrder(current);
                            current.append(_htmlResize($resizable.attr("data-id"), $resizable.css("top")));
                        }
                    }else {
                        let rs = current.find(".resizable").not($resizable);
                        if (rs.filter((d, i) => getTop($(rs[d])) === resizeTop).length > 0) {
                            reOrder(current, true, $resizable);
                        }
                    }
                }
            }else if (wDu > 0) {
                let itemOver = Math.floor(wDu/wHour);
                if (wDu%wHour > wHour/4) {
                    itemOver += 1;
                }
                let current = $target.parents(".r_item");
                let items = $resizable.parents('.w_item').find('.r_item');
                let indexItem = items.index(current);
                for (let i=0; i<itemOver; i++) {
                    current = right ? current.next() : current.prev();
                    let rs = current.find(".resizable");
                    let r = right ? rs.filter((d) => getTop($(rs[d])) === resizeTop && (getLeft($(rs[d])) > wHour/3 && getLeft($(rs[d])) < wHour/1.5)).length > 0
                        : rs.filter((d) => {
                        let _osL = getLeft($(rs[d]));
                        let _wRs = getWidth($(rs[d]));
                        _wRs += _osL > 0 ?_osL : 0;
                        return getTop($(rs[d])) === resizeTop && _wRs < wHour/1.5 && _wRs > wHour/3;
                    }).length > 0;
                    if (!(i === itemOver-1 && wDu%wHour < (wHour/2+5) && r)){
                        if (rs.filter((d) => $(rs[d]).attr("data-for") === $resizable.attr("data-id")).length === 0)  {
                            reOrder(current);
                            current.css({minHeight: (rs.length+1)*30+"px"});
                            current.append(_htmlResize($resizable.attr("data-id"), $resizable.css("top")))
                        }
                    }
                }
                let fReOrder = (i) => {
                    current = $(items[i]);
                    let rsFor = findRSFor(current);
                    if (rsFor.length > 0) {
                        let rs = $(rsFor[0]).parents('.r_item').find(".resizable");
                        reOrder($(rsFor[0]).parents('.r_item'), false);
                        current.css({minHeight: (rs.length-1)*30+"px"});
                        rsFor.remove();
                    }
                }
                let halfOrder = (i, rl=false) => {
                    if (wDu%wHour < (wHour/2+5) && wDu%wHour > wHour/4) {
                        current = $(items[i]);
                        let rs = current.find('.resizable');
                        let rsFor = findRSFor(current);
                        if (rsFor.length > 0 && rs.filter((d) => {
                            let _wRs = rl ? getLeft($(rs[d]))+getWidth($(rs[d])) : getLeft($(rs[d]));
                            return getTop($(rs[d])) === resizeTop+30 && _wRs  > wHour/4 && _wRs < wHour/1.5
                        }).length > 0) {
                            let rs = current.find(".resizable");
                            reOrder(current, false);
                            current.css({minHeight: (rs.length-1)*30+"px"});
                            rsFor.remove();
                        }
                    }
                }
                if (right) {
                    for (let i=indexItem+itemOver+1; i<items.length; i++) {
                        fReOrder(i);
                    }
                    halfOrder(indexItem+itemOver);
                }else {
                    for (let i = indexItem - itemOver - 1; i >= 0; i--) {
                        fReOrder(i);
                    }
                    halfOrder(indexItem - itemOver, true);
                }
            }
    },
    onResize: function (event) {
        let self = this;
        event.preventDefault();
        const {isManager} = this.model.data.data;
        if (isManager) {
            this.mouseDown = true;
            this.stopMove = true;
            var $target = $(event.target);
            let $resizable = $target.parents('.resizable');

            let resizeMove = (e) => {
                let wLeft = $target.parents('.w_container').find('.r_l')[0].getBoundingClientRect().width;
                if (e.pageX - wLeft > 0) {
                    if ($target.hasClass("right")) {
                        let wResizeable = e.pageX - $resizable.offset().left;
                        $resizable.css({width: wResizeable + 'px', zIndex: 3000});
                        self.resizeOver($resizable, $target);
                    } else {
                        let rWidth = $resizable[0].getBoundingClientRect().width;
                        $resizable.css({width: rWidth + ($resizable.offset().left - e.pageX) + 'px', zIndex: 3000});
                        $resizable.offset({left: e.pageX});
                        self.resizeOver($resizable, $target, false);
                    }
                }
                e.stopPropagation();
            }
            window.addEventListener('mousemove', resizeMove, true);
            let resizeDone = (e) => {
                // let $resizable = $target.parents('.resizable');
                let $rs = $target.parents('.w_item').find('.r_item');
                let wLeft = $target.parents('.w_container').find('.r_l')[0].getBoundingClientRect().width;
                let wHour = $resizable.parent()[0].getBoundingClientRect().width;
                let time = 0;
                let hours = $resizable.attr('hours');
                if ($target.hasClass("right")) {
                    let wResizeable = e.pageX - $resizable.offset().left;
                    let hour = Math.floor(wResizeable / wHour);
                    if (wResizeable % wHour >= wHour / 2) {
                        wResizeable = (hour + 1) * wHour;
                        time = hour + 1;
                    } else if (wResizeable % wHour >= (wHour / 2) / 2) {
                        wResizeable = hour * wHour + wHour / 2;
                        time = hour + 0.5;
                    } else {
                        wResizeable = hour * wHour;
                        time = hour;
                    }
                    hours = $rs.index($resizable.parents('.r_item'));
                    $resizable.css({width: wResizeable + 'px'});
                } else if (e.pageX - wLeft > 0) {
                    let rWidth = $resizable[0].getBoundingClientRect().width;
                    let wP = $resizable.offset().left - e.pageX;
                    let wResizeable = rWidth + wP;
                    let lOffset = e.pageX;
                    lOffset -= wLeft;
                    if (lOffset % wHour < wHour / 2) {
                        lOffset = Math.floor(lOffset / wHour) * wHour;
                        wResizeable += e.pageX - wLeft - lOffset;
                        time = Math.floor(wResizeable / wHour);
                        hours = Math.floor(lOffset / wHour);
                    } else if (lOffset % wHour > wHour / 2) {
                        lOffset = Math.floor(lOffset / wHour) * wHour + wHour / 2;
                        wResizeable += e.pageX - wLeft - lOffset;
                        time = Math.floor(wResizeable / wHour) + 0.5;
                        hours = Math.floor(lOffset / wHour) + 0.5;
                    } else {
                        lOffset = (Math.floor(wResizeable / wHour) + 1) * wHour;
                        wResizeable += e.pageX - wLeft - lOffset;
                        time = Math.floor(wResizeable / wHour) + 1;
                        hours = Math.floor(lOffset / wHour) + 1;
                    }
                    $resizable.css({width: wResizeable + 'px'});
                    $resizable.offset({left: lOffset + wLeft});
                } else {
                    let rWidth = $resizable[0].getBoundingClientRect().width;
                    let wP = $resizable.offset().left - wLeft;
                    let wResizeable = rWidth + wP;
                    $resizable.css({width: wResizeable + 'px'});
                    $resizable.offset({left: wLeft});
                    time = Math.floor(wResizeable / wHour);
                    if (wResizeable % wHour >= wHour / 2) {
                        time = time + 1;
                    } else if (wResizeable % wHour >= (wHour / 2) / 2) {
                        time = time + 0.5;
                    }
                    hours = 0;
                }
                self.updateData(self.getData($resizable, hours, time));
                $resizable.css({zIndex: 100});
                $resizable.attr({time: time, hours: hours});
                this.setDisplayTime($resizable);
                window.removeEventListener('mouseup', resizeDone, true);
                window.removeEventListener('mousemove', resizeMove, true);
                this.stopMove = false;
                e.stopPropagation();
            }
            window.addEventListener('mouseup', resizeDone, true);
        }
    },
    // convertTimeZone: function (date) {
    //     var offset = this.getSession().getTZOffset(date);
    //     return date.clone().add(offset, 'minutes');
    // },
    getData: function ($resizable, hours, time) {
        let {staff_data} = this.model.data.data;
        let viewType = this.model.viewType;
        let $rItem = $resizable.parents('.w_item').find('.r_item');
        let data_id = parseInt($resizable.attr('data-data'));
        let item = staff_data.filter((d) => d.id === data_id);
        let iStart = Math.floor(hours/1);
        let iEnd = Math.floor((time+hours-1)/1);
        if ($rItem.attr("data-hour")) {
            iEnd = Math.floor((time+hours)/1);
        }
        let start_date = $($rItem[iStart]).attr("data-date");
        let end_date = $($rItem[iEnd]).attr("data-date");
        if (item.length > 0) {
            let _start_date = this.convertTimeZone(moment(item[0].start_date, "YYYY-MM-DD HH:mm:ss"));
            let _end_date = this.convertTimeZone(moment(item[0].end_date, "YYYY-MM-DD HH:mm:ss"));
            let startHours = _start_date.hour(),
                endHours = _end_date.hour();
            let startMinutes = _start_date.minute(),
                endMinutes = _end_date.minute();
            if (viewType !== "day") {
                start_date = moment(start_date, "YYYY-MM-DD HH:mm:ss").set('hour', startHours)
                end_date = moment(end_date, "YYYY-MM-DD HH:mm:ss").set('hour', endHours)
            }
                // else {
            //
            // }
            // start_date = moment(start_date, "YYYY-MM-DD HH:mm:ss").set('minute', startMinutes).format("YYYY-MM-DD HH:mm:ss")
            // end_date = moment(end_date, "YYYY-MM-DD HH:mm:ss").set('minute', endMinutes).format("YYYY-MM-DD HH:mm:ss")

            start_date = moment(start_date, "YYYY-MM-DD HH:mm:ss").set('minute', startMinutes)
            end_date = moment(end_date, "YYYY-MM-DD HH:mm:ss").set('minute', endMinutes)
            start_date = start_date.subtract(this.getSession().getTZOffset(start_date), "minutes")
            end_date = end_date.subtract(this.getSession().getTZOffset(end_date), "minutes")
        }

        return {id: data_id, values: {start_date: start_date.format("YYYY-MM-DD HH:mm:ss"), end_date: end_date.format("YYYY-MM-DD HH:mm:ss")}};
    },
    updateData: function (data) {
        let self = this;
        return self.model.onWrite(data.id, data.values).then((d) => {
            self.model._loadData().then((d) => {
                self.update({data: self.model.data}, {reload: false});
            });
        });
    },
    updateDrop: function () {

    },
    /**
     * @override
     */
    start: function () {
        return this._super();
    },
    /**
     * @override
     */
    destroy: function () {
        if (this.$buttons) {
            // remove jquery's tooltip() handlers
            this.$buttons.find('button').off();
        }
        return this._super.apply(this, arguments);
    },

    /**
     * Render the buttons according to the PivotView.buttons template and
     * add listeners on it.
     * Set this.$buttons with the produced jQuery element
     *
     * @param {jQuery} [$node] a jQuery node where the rendered buttons should
     *   be inserted. $node may be undefined, in which case the PivotView
     *   does nothing
     */
    renderButtons: function ($node) {

        if ($node) {
            const {outlet_manager_ids, isManager} = this.model.data.data;
            this.$buttons = $(QWeb.render('StaffPlanning.buttons', {outlet_manager: outlet_manager_ids.length > 0 ? true:false, isManager: isManager}));
            this.$buttons.find(".btn-t.o_staff_week").addClass("active");
            this.$buttons.find(".btn-s.o_staff_employee").addClass("active");
            this.$buttons.click(this._onButtonClick.bind(this));
            this.$buttons.find('button').tooltip();
            this.$buttons.appendTo($node);
            this._renderOutlet($node);
            this._updateButtons();
        }
    },
    onSearchOutlet: function (outletID) {
        let self = this;
        let domain = this.getDomain();
        domain = domain.concat([['outlet_id', '=', outletID]]);
        this.model.onSearch(domain).then((d) => {
            self.update({}, {reload: false});
        });
    },
    _renderOutlet: function ($node) {
        if (!this.outlet) {
            var self = this;
            var {outlet_manager_ids} = self.model.data.data;
            var $wrapOutlet = $(`<div style="display: flex;padding: 5px;"><label style="font-size: 15px;padding-right: 10px; font-weight: bold;">Outlet</label><div class="wOutlet"></div></div>`);
            var BasicModel = require('web.BasicModel');
            var widget = new Widget();
            var model = new BasicModel(widget);

            model.makeRecord("stock.warehouse", [{
                name: "outlet_id",
                string: "Outlet",
                relation: "stock.warehouse",
                domain: [['id', 'in', outlet_manager_ids]],
                type: 'many2one'
            }]).then((recordID) => {
                var record = model.get(recordID);
                self.outlet = new FieldMany2One(self, 'outlet_id', record, {
                    mode: 'edit',
                    noOpen: true,
                    attrs: {
                        can_create: false
                    },
                });
                let _onFieldChanged = self.outlet._onFieldChanged.bind(self.outlet);
                let _onInputKeyup = self.outlet._onInputKeyup.bind(self.outlet);
                self.outlet._onInputKeyup = (ev) => {
                    _onInputKeyup(ev);
                    if (self.outlet.$input.val() === "") {
                        self.onSearchOutlet(false);
                    }
                }
                self.outlet._onFieldChanged = (event) => {
                    _onFieldChanged(event);
                    let outletData = self.outlet.lastSetValue;
                    self.outlet.$input.val(outletData.display_name);
                    self.onSearchOutlet(outletData.id);
                }
                self.outlet.appendTo($wrapOutlet.find('.wOutlet'));
                $wrapOutlet.appendTo($node.find('.last-gr'));
            })
        }
    },
    /**
     * @private
     */
    _update: function () {
        // this._updateButtons();
        var {outlet_manager_ids} = this.model.data.data;
        if (!outlet_manager_ids.length) {
            this.$buttons.find('.o_staff_employee').css({display: 'none'});
            this.$buttons.find('.o_staff_role').css({display: 'none'});
        }
        if (this.model.viewType === 'week') {
            this.$buttons.find('.o_staff_copy_week').css({display: 'inline-block'});
        }else {
            this.$buttons.find('.o_staff_copy_week').css({display: 'none'});
        }
        return this._super.apply(this, arguments);
    },
    /**
     * @private
     */
    _updateButtons: function () {
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * This handler is called when the user clicked on a button in the control
     * panel.  We then have to react properly: it can either be a change in the
     * current measures, or a request to flip/expand/download data.
     *
     * @private
     * @param {MouseEvent} event
     */
    setState: function (data) {
        Object.keys(data).map((d, i) => this.model[d] = data[d]);
        this.update({}, {reload: false});
    },
    getDomain: function (prev) {
        let domain = [];
        let viewType = this.model.getView();
        let strFormat = "YYYY-MM-DD HH:mm:ss";
        let sDate = null;
        let eDate = null;
        let week = prev ? this.week - 1 : this.week;

        let _day = moment().add(this.day, 'days');
        _day.add(week, 'weeks')
        _day.add(this.month, 'months')

        if (viewType === 'week') {
            // let monday = _day
            // let monday = moment().startOf('week');
            // let week = moment(monday).add(day, 'weeks');
            let week = _day.clone()
            sDate = week.startOf("weeks");
            eDate = week.clone().endOf("weeks");

        }else if (viewType === 'month') {
            sDate = _day.clone().startOf('month');
            eDate = _day.clone().endOf('month');
            // domain.push(['start_date', '>=', sDate], ['end_date', '<=', eDate]);
        }else {
            sDate = _day.clone().startOf('date');
            eDate = _day.clone().endOf('date');
        }
        sDate = this.convertTimeZone(sDate, false);
        eDate = this.convertTimeZone(eDate, false);
        domain.push(['start_date', '>=', sDate.format(strFormat)], ['end_date', '<=', eDate.format(strFormat)]);
        console.log(domain);
        return domain;
    },
    onChangeDay: function (day) {
        let self = this;
        this.model.onSearch(this.getDomain()).then(function () {
            self.setState({viewData: self.day, day: self.day, week: self.week, month: self.month, data: self.model.data});
        });
    },
    getDataSendSchedule: function () {
        let viewData = this.model.viewData;
        let viewType = this.model.getView();
        let {staff_data} = this.model.data.data;
        // let employees = staff_data.map((d, i) => d.employee_id[0]);
        let format = 'YYYY-MM-DD HH:mm:ss';
        let data = {start_date: moment(), end_date: moment()};
        if (viewType === 'day') {
            data.start_date = data.start_date.startOf('day');
            data.start_date = data.start_date.endOf('day');
        } else if (viewType === 'week') {
            data.start_date.startOf('week');
            data.start_date = moment(data.start_date).add(viewData, 'weeks').startOf('days');
            data.end_date = moment(data.start_date).add(6, 'days').endOf('days');
        } else if (viewType === 'month') {
            data.start_date.startOf('month');
            data.start_date = moment(data.start_date).add(viewData, 'month').startOf('month');
            data.end_date = data.start_date.endOf('month');
        }
        data.start_date = data.start_date.format(format);
        data.end_date = data.end_date.format(format);
        return data;
    },
    _onButtonClick: function (event) {
        let self = this;
        var $target = $(event.target);
        if ($target.hasClass('o_staff_add')) {
            let ctx = {
                outlet: self.outlet.lastSetValue ? self.outlet.lastSetValue.id : false,
            };
            this.model.onShowCreate(false, () => {
                self.model._loadData().then((d) => {
                    self.update({data: self.model.data}, {reload: false});
                });
            }, () => {
            }, ctx);
        }
        if ($target.hasClass('o_staff_send_schedule')) {
            this.model.createSendSchedule(this.getDataSendSchedule()).then((r) => {
                if (r) {
                    self.model.onShowSendSchedule(r);
                }
            });
        }
        let viewType = this.model.viewType;
        if ($target.hasClass('o_staff_prev')) {
            switch (viewType) {
                case "day":
                    this.day -= 1;
                    break;
                case "week":
                    this.week -= 1;
                    break;
                case "month":
                    this.month -= 1;
                    break;
            }

            this.onChangeDay();
        }
        if ($target.hasClass('o_staff_today')) {
            this.day = 0;
            this.week = 0;
            this.month = 0;
            this.onChangeDay();
        }
        if ($target.hasClass('o_staff_next')) {
            switch (viewType) {
                case "day":
                    this.day += 1;
                    break;
                case "week":
                    this.week += 1;
                    break;
                case "month":
                    this.month += 1;
                    break;
            }
            this.onChangeDay();
        }
        if ($target.hasClass('btn-expand')) {
            this.$el.find('.w_body_group').css({display: $target.hasClass('o_staff_expand_rows') ? 'block' : 'none'})
        }
        if ($target.hasClass('fa-expand')) {
            this.$el.find('.w_body_group').css({display: 'block'})
        }
        if ($target.hasClass('fa-compress')) {
            this.$el.find('.w_body_group').css({display: 'none'})
        }
        if ($target.hasClass('btn-s')) {
            this.$buttons.find(".btn-s").removeClass("active");
            $target.addClass("active");
            if ($target.hasClass('o_staff_employee')) {
                // this.$buttons.parent().find('.btn-group.expand, .o_staff_copy_week').css({display: 'none'})
                this.setState({viewGroup: "employee"});
            }
            if ($target.hasClass('o_staff_role')) {
                // this.$buttons.parent().find('.btn-group.expand, .o_staff_copy_week').css({display: 'inline-block'});
                this.setState({viewGroup: "role"});
            }
        }
        if ($target.hasClass("o_staff_copy_week")) {
            let format = "YYYY-MM-DD HH:mm:ss";
            this.model.onSearch(this.getDomain(true)).then(function () {
                let {staff_data} = self.model.data.data;
                staff_data.map((d, i) => {
                    d.start_date = moment(d.start_date, format).add(1, 'weeks').format(format);
                    d.end_date = moment(d.end_date, format).add(1, 'weeks').format(format);
                    d.employee_id = d.employee_id[0];
                    d.role_id = d.role_id ? d.role_id[0] : false;
                    d.company_id = d.company_id ? d.company_id[0] : false;
                    return d;
                });
                self.model.copyPreviousWeek(staff_data).then((d) => {
                    self.onChangeDay();
                });
            });

        }
        if ($target.hasClass('btn-t')) {
            this.$buttons.find(".btn-t").removeClass("active");
            $target.addClass("active");
            if ($target.hasClass('o_staff_day')) {
                this.model.setView('day');
                this._reload();
                // this.update({}, {reload: false});
            }
            if ($target.hasClass('o_staff_week')) {
                this.model.setView('week');
                this._reload();
                // this.update({}, {reload: false});
            }
            if ($target.hasClass('o_staff_month')) {
                this.model.setView('month');
                this._reload();
                // this.update({}, {reload: false});
            }
        }
    },
    _reload: function () {
        let self = this;
        this.model.onSearch(this.getDomain()).then(function () {
            self.setState({data: self.model.data});
        });
    }
});

return StaffPlanningController;

});
