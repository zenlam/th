odoo.define('th_promotion.promotion', function (require) {
"use strict";

    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var screens = require('point_of_sale.screens');

    var QWeb = core.qweb;

    var PromotionHeaderWidget = PosBaseWidget.extend({
        template: 'PromotionHeaderWidget',
        init: function (parent, options) {
            this._super(parent, options);
            this.props = options;
            const {searchFor} = this.props;
            this.promotionView = parent;
            this.searchInfo = {promotion: {label: 'Search Promotion', search: this.searchPromotion.bind(this), domain: this.domainPromotion.bind(this)},
                rule: {label: 'Search Rule' , search: this.searchRule.bind(this), domain: this.domainRule.bind(this)},
                product: {label: 'Search Product' , search: this.searchProduct.bind(this), domain: this.domainProduct.bind(this)}};
            this.current = this.searchInfo[searchFor];
        },
        domainPromotion: function (value) {
            let domain = [['name', 'like', value]];
            return domain;
        },
        domainProduct: function (value) {
            let domain = [['display_name', 'like', value]];
            return domain;
        },
        domainRule: function (value) {
            let domain = [['name', 'like', value]];
            return domain;
        },
        onSearch: function (domain) {
            this.current.search(domain);
        },
        searchPromotion: function (domain) {
            this.promotionView.model.searchPromotion(domain);
        },
        searchRule: function (domain) {
            this.promotionView.model.searchRule(domain);
        },
        searchProduct: function (domain) {
            this.promotionView.onSearchProduct(domain);
        },
        onClickBack: function () {
            const {onBack} = this.props;
            onBack();
        },
        setSearchFor: function (searchFor) {
            this.current = this.searchInfo[searchFor];
            this.$el.find('.inputSearch').attr("placeholder", this.current.label);
        },
        onClickHome: function () {
            let {products, promotions_screen} = this.promotionView.screensInstance;
            products.setOrderWidget(promotions_screen.orderWidget);
            this.gui.show_screen('products');
        },
        showBack: function (show) {
            this.$el.find('.btnBack').css({display: show ? 'block' : 'none'});
        },
        onKeyPress: function (event) {
            this.onSearch(this.current.domain(event.currentTarget.value));
        },
        bindAction: function () {
            this.el.querySelector('.back-home').addEventListener('click', this.onClickHome.bind(this));
            this.$el.find('.btn-back').click(this.onClickBack.bind(this));
            this.$el.find('.inputSearch').keyup(this.onKeyPress.bind(this));
        },
        renderElement: function () {
            this._super();
            this.bindAction();
        }
    });

    var PromotionProductView = PosBaseWidget.extend({
        template: 'PromotionProductView',
        init: function (parent, options) {
            this._super(parent, options);
            this.props = options;
        },
        onClickProduct: function () {
            const {onClickProduct} = this.props;
            onClickProduct();
        },
        renderContent: function () {
            let self = this;
            this.productView = new screens.ProductListWidget(this, {
                click_product_action: self.onClickProduct.bind(this),
                product_list: this.pos.db.get_product_by_category(0)
            });
            this.productView.renderElement();
            this.$el.find('.promotion-list').append(this.productView.el);
        },
        renderElement: function () {
            this._super();
            this.renderContent();
        },
    });

    var PromotionRuleView = PosBaseWidget.extend({
        template: 'PromotionRuleView',
        init: function (parent, options) {
            this._super(parent, options);
            this.props = options;
            this.data = options.rules || {};
            this.promotion = options.promotion;
        },
        onClickRule: function () {
            const {onClickRule} = this.props;
            onClickRule();
        },
        onKeypressRule: function () {
            // do something
        },
        bindAction: function ($rule, rule) {
            $rule[0].addEventListener('click', () => this.onClickRule.bind(this)(rule));
            $rule[0].addEventListener('keypress', () =>  this.onKeypressRule.bind(this)(rule));
        },
        renderItem: function(rule){
            let ruleHtml = QWeb.render('PromotionItem',{
                widget:  this,
                ...rule
            });
            return $(ruleHtml);
        },
        renderLine: function () {
            let self = this;
            let $ruleLine = QWeb.render('RuleLine', {
                widget:  this
            });
            $ruleLine = $($ruleLine);
            Object['keys'](this.data).map((ruleID) => {
                const rule = this.data[ruleID], $rule = self.renderItem(rule);
                self.bindAction($rule, rule);
                $ruleLine.find('.line-container').append($rule);
            });
            return $ruleLine;
        },
        renderContent: function () {
            this.$el.find('.promotion-list').append(this.renderLine());
        },
        renderElement: function () {
            this._super();
            this.renderContent();
        },
    });
    var PromotionListWidget = PosBaseWidget.extend({
        template: 'PromotionListWidget',
        init: function (parent, options) {
            this._super(parent, options);
            this.promotionView = parent;
            this.promotions = options.promotions || {};
            // this.promotionCache = new screens.DomCache();
            this.props = options;
            this.group = true;
            if (options.hasOwnProperty('group')) {
                this.group = options.group;
            }
            this.data = this.prepareData();
        },
        prepareData: function () {
            let promotionType = {bill: {name: 'bill', label: 'Bill Discount', promotions: {}},
                product: {name: 'product', label: 'Product Discount', promotions: {}}};
            Object['keys'](this.promotions).map((promotionId) => {
                let promotion = this.promotions[promotionId], {obj} = promotion;
                promotionType[obj['apply_for']].promotions[promotionId] = promotion;
            });
            if (!this.group) {
                let noGroupData = {none: {label: false, name: 'none', promotions: this.promotions}};
                return noGroupData;
            }
            return promotionType;
        },
        onClickPromotion: function (promotion) {
            const {onClickPromotion} = this.props;
            onClickPromotion(promotion);
        },
        onKeypressPromotion: function () {
            alert("onKeypress");
        },
        bindActionPromotion: function ($promotion, promotion) {
            $promotion[0].addEventListener('click', () => this.onClickPromotion.bind(this)(promotion));
            $promotion[0].addEventListener('keypress', () =>  this.onKeypressPromotion.bind(this)(promotion));
        },
        renderGroup: function (data, $container) {
            let self = this;
            Object['keys'](data).map((promotionType) => {
                const {promotions, label} = data[promotionType];
                let promotionLine = QWeb.render('PromotionLine', {
                    widget:  this,
                    name: label,
                });
                promotionLine = $(promotionLine);
                Object['keys'](promotions).map((proKey) => {
                    const promotion = promotions[proKey];
                    let $promotion = self.renderItem(promotion.obj);
                    self.bindActionPromotion($promotion, promotion);
                    promotionLine.find('.line-container').append($promotion);
                });
                $container.append(promotionLine);
            });
        },
        renderContainer: function () {
            let $container = $(`<div class="wLine">`);
            this.renderGroup(this.data, $container);
            this.$('.promotion-list').append($container);
        },
        renderItem: function(promotion){
            let promotionHtml = QWeb.render('PromotionItem',{
                widget:  this,
                ...promotion
            });
            return $(promotionHtml);
        },
        renderElement: function() {
            this._super();
            this.renderContainer();
        },
    });

    var PromotionScreenWidget = screens.ScreenWidget.extend({
        template:'PromotionScreenWidget',
        init: function (parent, options) {
            this._super(parent, options);
            this.props = options;
            this.view = {stack: []};
            this.promotions = options.promotions || {};
            // this.stackContentView = [];
            this.step = 'promotion';
            this.stackStep = [];
            this.stepRender = {
                promotion: {render: (params) => this.renderPromotion.bind(this)(params), next: 'rule'},
                rule: {render: (params) => this.renderRule.bind(this)(params), next: 'product'},
                product: {render: (params) => this.renderProduct.bind(this)(params), next: 'rule', back: true}
            };
            this.model = new models.Promotion({}, {pos: this.pos});
            this.pos.modelInstance = {};
            this.pos.modelInstance['promotion'] = this.model;
        },
        start: function(){
            // this.model = new models.Promotion({}, {pos: this.pos});
            // this.pos.modelInstance = {};
            // this.pos.modelInstance['promotion'] = this.model;
        },
        show: function () {
            this._super();
            if (this.view.stack.length <= 1) {
                let getScreenParams = (paramName) => this.gui.get_current_screen_param(paramName);
                this.promotions = getScreenParams('promotions');
                this.screensInstance = getScreenParams('screensInstance');
                this.reloadContent({promotions: this.promotions});
            }
        },
        getStackLength: function () {
            return this.stackStep.length;
        },
        reloadContent: function (params={}) {
            this.clearContainer();
            this.renderContent({fromReload: true});
        },
        setOrderWidget: function (orderWidget) {
            this.orderWidget = orderWidget;
            this.renderOrder();
        },
        setStep: function (step) {
            this.switchView(step);
        },
        switchView: function (step, params={}) {
            this.step = step;
            this.clearContainer();
            let newView = this.stepRender[step].render(params);
            params.fromReload ? this.view.stack.pop() : this.stackStep.push(step);
            this.view.stack.push(newView);
            this.replaceContainer(newView);
            this.view.header.showBack(this.view.stack.length > 1);
            this.view.header.setSearchFor(this.step);
        },
        replaceContainer: function (newView) {
            this.view.container = newView;
            this.view.container.replace(this.$('.placeholder-PromotionListWidget'));
        },
        clearContainer: function () {
            this.$el.find('.content-container :first-child').replaceWith($('<div class="placeholder-PromotionListWidget">'));
        },
        onClickRuleItem: function (rule) {
            let step = this.stepRender[this.step].next;
            this.switchView(step, {rule: rule});
        },
        onClickPromotionItem: function (promotion) {
            let step = this.stepRender[this.step].next;
            this.switchView(step, {promotion: promotion});
        },
        onSearchProduct: function (domain) {
            let productList = this.model.searchProduct(domain);
            this.view.container.productView.set_product_list(productList);
        },
        goPreviousView: function () {
            let {stack} = this.view;
            this.view.stack.pop();
            this.stackStep.pop();
            this.step = this.stackStep[this.stackStep.length - 1];
            const previousView = stack[stack.length - 1];
            this.clearContainer();
            this.replaceContainer(previousView);
            this.view.header.showBack(this.view.stack.length > 1);
            this.view.header.setSearchFor(this.step);
        },
        onClickProductItem: function (product) {
            const step = this.stepRender[this.step], {back, next} = step;
            back ? this.goPreviousView() : this.switchView(next, {product: product});
        },
        renderPromotion: function (params) {
            let group = this.props.hasOwnProperty('group') ? this.props.group : true;
            return new PromotionListWidget(this, {onClickPromotion: this.onClickPromotionItem.bind(this), group: group,
                promotions: this.promotions || {}, ...params});
        },
        renderRule: function (params) {
            return new PromotionRuleView(this, {onClickRule: this.onClickRuleItem.bind(this), rules: params.promotion.rules || {}});
        },
        renderProduct: function (params) {
            return new PromotionProductView(this, {onClickProduct: this.onClickProductItem.bind(this), ...params});
        },
        renderHeader: function () {
            this.view.header = new PromotionHeaderWidget(this, {onBack: this.goPreviousView.bind(this), searchFor: this.step});
            this.view.header.replace(this.$('.placeholder-PromotionWidget'));
        },
        renderContent: function (params) {
            this.switchView(this.step, params);
        },
        renderOrder: function () {
            this.$el.find('.placeholder-OrderWidget').html(this.orderWidget.el);
        },
        renderElement: function () {
            this._super();
            this.renderHeader();
            this.renderContent();
        }
    });

    gui.define_screen({name:'promotions_screen', widget: PromotionScreenWidget});

    return {PromotionListWidget: PromotionListWidget, PromotionScreenWidget: PromotionScreenWidget}
});
