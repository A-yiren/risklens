"""合同中心的共用模板目录。

模板将“官方示范文本参照”和“平台结构草稿”明确区分。草稿只填入用户在
表单中确认的事实；缺失字段保持可见占位符，避免把推测写入合同。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


OFFICIAL_LIBRARY = "https://htsfwb.samr.gov.cn/"
LABOR_LAW = "https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/zcfg/fl/202011/t20201102_394622.html"


@dataclass(frozen=True)
class TemplateField:
    key: str
    label: str
    kind: str = "text"
    required: bool = False
    placeholder: str = ""
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class TemplateSection:
    title: str
    body: str


@dataclass(frozen=True)
class ContractTemplate:
    template_id: str
    name: str
    category: str
    description: str
    review_contract_type: str
    source_kind: str
    publisher: str
    source_url: str
    source_note: str
    fields: tuple[TemplateField, ...]
    sections: tuple[TemplateSection, ...]


def _field(key: str, label: str, *, required: bool = False, kind: str = "text", placeholder: str = "", options: tuple[str, ...] = ()) -> TemplateField:
    return TemplateField(key, label, kind, required, placeholder, options)


COMMON_FIELDS = (
    _field("party_a", "甲方名称", required=True, placeholder="个人姓名或单位全称"),
    _field("party_b", "乙方名称", required=True, placeholder="个人姓名或单位全称"),
    _field("signing_date", "签订日期", required=True, kind="date"),
    _field("dispute_resolution", "争议解决", kind="textarea", placeholder="协商不成时的诉讼或仲裁安排"),
)


TEMPLATES: tuple[ContractTemplate, ...] = (
    ContractTemplate(
        template_id="residential_lease",
        name="城镇房屋租赁合同",
        category="居住与租赁",
        description="适用于个人或单位出租城镇房屋的常用场景。",
        review_contract_type="lease",
        source_kind="official_reference",
        publisher="国家市场监督管理总局",
        source_url="https://htsfwb.samr.gov.cn/View?id=2340996b-882d-47a4-b74d-c30784628737",
        source_note="参照城镇房屋租赁合同示范文本的结构；平台生成的是可编辑草稿，不是官方表单原件。",
        fields=(
            _field("landlord", "出租人", required=True), _field("tenant", "承租人", required=True),
            _field("property_address", "房屋地址", required=True), _field("lease_use", "租赁用途", required=True, options=("住宅", "办公", "商业"), kind="select"),
            _field("lease_start", "租赁开始日期", required=True, kind="date"), _field("lease_end", "租赁结束日期", required=True, kind="date"),
            _field("rent", "租金金额（元）", required=True, kind="number"), _field("rent_frequency", "租金支付周期", required=True, kind="select", options=("每月", "每季度", "每半年", "每年")),
            _field("deposit", "押金金额（元）", kind="number"), _field("handover", "交付与验收约定", kind="textarea"),
            _field("maintenance", "维修与费用承担", kind="textarea"), _field("dispute_resolution", "争议解决", kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 当事人及租赁房屋", "出租人（甲方）：{landlord}\n承租人（乙方）：{tenant}\n甲方将位于{property_address}的房屋交由乙方使用，租赁用途为{lease_use}。"),
            TemplateSection("第二条 租赁期限、租金与押金", "租赁期限自{lease_start}起至{lease_end}止。租金为人民币{rent}元，按{rent_frequency}支付。押金：{deposit}。"),
            TemplateSection("第三条 交付、维修、解除与争议", "交付与验收：{handover}\n维修及费用承担：{maintenance}\n争议解决：{dispute_resolution}"),
        ),
    ),
    ContractTemplate(
        template_id="labor_contract",
        name="劳动合同",
        category="就业与人事",
        description="适用于用人单位与劳动者建立劳动关系。",
        review_contract_type="labor",
        source_kind="statutory_required_terms",
        publisher="人力资源和社会保障部",
        source_url=LABOR_LAW,
        source_note="按劳动合同法第十七条必备条款组织；试用期、工时、工资和社保须结合当地规则与实际情况复核。",
        fields=(
            _field("employer", "用人单位", required=True), _field("employee", "劳动者", required=True),
            _field("term_type", "合同期限类型", required=True, kind="select", options=("固定期限", "无固定期限", "以完成一定工作任务为期限")),
            _field("start_date", "合同开始日期", required=True, kind="date"), _field("end_date", "合同结束日期", kind="date"),
            _field("position", "工作岗位", required=True), _field("workplace", "工作地点", required=True),
            _field("working_hours", "工时制度", required=True, kind="select", options=("标准工时", "综合计算工时", "不定时工作制")),
            _field("salary", "工资标准（元/月）", required=True, kind="number"), _field("payday", "工资支付日", required=True),
            _field("social_insurance", "社会保险约定", required=True, kind="textarea"), _field("probation", "试用期约定", kind="textarea"),
            _field("confidentiality", "保密或竞业限制约定", kind="textarea"), _field("termination", "解除终止约定", kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 当事人和合同期限", "用人单位（甲方）：{employer}\n劳动者（乙方）：{employee}\n本合同为{term_type}，自{start_date}起至{end_date}止。"),
            TemplateSection("第二条 工作内容、地点与工时", "乙方岗位：{position}；工作地点：{workplace}。工时制度：{working_hours}。"),
            TemplateSection("第三条 劳动报酬、社会保险与劳动保护", "工资标准：人民币{salary}元/月；工资支付日：{payday}。\n社会保险：{social_insurance}"),
            TemplateSection("第四条 其他约定", "试用期：{probation}\n保密及竞业限制：{confidentiality}\n解除、终止及违约处理：{termination}"),
        ),
    ),
    ContractTemplate(
        template_id="labor_service_contract",
        name="劳务服务合同",
        category="就业与人事",
        description="适用于独立劳务提供、项目协作等非当然劳动关系场景。",
        review_contract_type="service",
        source_kind="platform_structured_draft",
        publisher="RiskLens 合同中心",
        source_url=OFFICIAL_LIBRARY,
        source_note="劳务与劳动关系的认定高度依赖实际履行；本草稿不替代劳动关系认定或用工合规审查。",
        fields=(
            _field("client", "委托方", required=True), _field("provider", "劳务提供方", required=True),
            _field("service_content", "劳务内容", required=True, kind="textarea"), _field("service_location", "服务地点", required=True),
            _field("start_date", "开始日期", required=True, kind="date"), _field("end_date", "结束日期", required=True, kind="date"),
            _field("fee", "劳务报酬（元）", required=True, kind="number"), _field("payment", "支付方式与节点", required=True, kind="textarea"),
            _field("acceptance", "成果或服务确认方式", required=True, kind="textarea"), _field("safety", "安全与责任约定", kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 劳务事项", "委托方（甲方）：{client}\n劳务提供方（乙方）：{provider}\n乙方提供的劳务内容：{service_content}。服务地点：{service_location}。"),
            TemplateSection("第二条 服务期限与报酬", "服务期限自{start_date}起至{end_date}止。劳务报酬为人民币{fee}元。支付安排：{payment}"),
            TemplateSection("第三条 确认、安全与责任", "成果或服务确认：{acceptance}\n安全及责任安排：{safety}"),
        ),
    ),
    ContractTemplate(
        template_id="goods_sale_contract",
        name="商品买卖合同",
        category="交易与采购",
        description="适用于明确标的、数量、质量、交付和价款的商品交易。",
        review_contract_type="sale",
        source_kind="official_reference",
        publisher="国家市场监督管理总局合同示范文本库",
        source_url="https://htsfwb.samr.gov.cn/List?key=%E4%B9%B0%E5%8D%96",
        source_note="参照合同示范文本库中买卖类文本的基础结构；具体商品应补充行业标准、检验与售后规则。",
        fields=(
            _field("seller", "出卖人", required=True), _field("buyer", "买受人", required=True),
            _field("goods", "商品名称及型号", required=True), _field("quantity", "数量与单位", required=True),
            _field("quality", "质量标准", required=True, kind="textarea"), _field("total_price", "合同总价（元）", required=True, kind="number"),
            _field("payment", "付款方式", required=True, kind="textarea"), _field("delivery", "交付时间与地点", required=True, kind="textarea"),
            _field("acceptance", "验收方式与异议期限", required=True, kind="textarea"), _field("warranty", "质保或售后约定", kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 标的与质量", "出卖人（甲方）：{seller}\n买受人（乙方）：{buyer}\n商品：{goods}\n数量：{quantity}\n质量标准：{quality}"),
            TemplateSection("第二条 价款、付款与交付", "合同总价为人民币{total_price}元。付款方式：{payment}\n交付安排：{delivery}"),
            TemplateSection("第三条 验收、售后与违约", "验收与异议：{acceptance}\n质保或售后：{warranty}\n未约定事项由双方依法协商处理。"),
        ),
    ),
    ContractTemplate(
        template_id="service_contract",
        name="服务合同",
        category="交易与采购",
        description="适用于咨询、运营、技术支持、培训等服务采购。",
        review_contract_type="service",
        source_kind="official_reference",
        publisher="国家市场监督管理总局合同示范文本库",
        source_url="https://htsfwb.samr.gov.cn/List?key=%E6%9C%8D%E5%8A%A1",
        source_note="参照服务类示范文本结构；行业准入、资质、数据与个人信息要求须另行核对。",
        fields=(
            _field("client", "委托方", required=True), _field("provider", "服务方", required=True),
            _field("scope", "服务范围", required=True, kind="textarea"), _field("standard", "服务标准", required=True, kind="textarea"),
            _field("start_date", "开始日期", required=True, kind="date"), _field("end_date", "结束日期", required=True, kind="date"),
            _field("fee", "服务费（元）", required=True, kind="number"), _field("payment", "支付节点", required=True, kind="textarea"),
            _field("acceptance", "验收方式", required=True, kind="textarea"), _field("ip", "成果知识产权归属", kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 服务事项", "委托方（甲方）：{client}\n服务方（乙方）：{provider}\n服务范围：{scope}\n服务标准：{standard}"),
            TemplateSection("第二条 服务期限与费用", "服务期限自{start_date}起至{end_date}止。服务费为人民币{fee}元，支付节点：{payment}"),
            TemplateSection("第三条 验收、成果与保密", "验收方式：{acceptance}\n知识产权归属：{ip}\n双方对履约中知悉的非公开信息承担合理保密义务。"),
        ),
    ),
    ContractTemplate(
        template_id="entrustment_contract",
        name="委托合同",
        category="委托与合作",
        description="适用于委托他人处理事务、提供代理或综合服务。",
        review_contract_type="service",
        source_kind="official_reference",
        publisher="国家市场监督管理总局",
        source_url="https://htsfwb.samr.gov.cn/View?id=50b57729-0fca-45d2-92c3-fe7e6a989815",
        source_note="参照 GF—2025—1001 委托合同示范文本；应特别确认授权范围、转委托和解除后的费用结算。",
        fields=(
            _field("principal", "委托人", required=True), _field("agent", "受托人", required=True),
            _field("matters", "委托事项", required=True, kind="textarea"), _field("authority", "授权范围", required=True, kind="textarea"),
            _field("start_date", "委托开始日期", required=True, kind="date"), _field("end_date", "委托结束日期", required=True, kind="date"),
            _field("fee", "委托费用（元）", required=True, kind="number"), _field("payment", "费用支付方式", required=True, kind="textarea"),
            _field("reporting", "报告与交付要求", kind="textarea"), _field("subdelegate", "是否允许转委托", kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 委托事项与权限", "委托人（甲方）：{principal}\n受托人（乙方）：{agent}\n委托事项：{matters}\n授权范围：{authority}"),
            TemplateSection("第二条 期限、费用与报告", "委托期限自{start_date}起至{end_date}止。委托费用为人民币{fee}元，支付方式：{payment}\n报告与交付：{reporting}"),
            TemplateSection("第三条 转委托、解除与责任", "转委托安排：{subdelegate}\n双方应就任意解除、费用结算、资料返还与损失承担作出明确约定。"),
        ),
    ),
    ContractTemplate(
        template_id="confidentiality_agreement",
        name="保密协议",
        category="委托与合作",
        description="适用于商务洽谈、合作、技术与经营信息披露前后。",
        review_contract_type="general",
        source_kind="platform_structured_draft",
        publisher="RiskLens 合同中心",
        source_url=OFFICIAL_LIBRARY,
        source_note="保密义务应与具体信息、用途、期限和违约后果对应；涉及个人信息或数据出境时需另行合规评估。",
        fields=(
            _field("discloser", "信息披露方", required=True), _field("recipient", "信息接收方", required=True),
            _field("confidential_info", "保密信息范围", required=True, kind="textarea"), _field("purpose", "允许使用目的", required=True, kind="textarea"),
            _field("term", "保密期限", required=True), _field("return_terms", "返还、销毁与留存规则", required=True, kind="textarea"),
            _field("exceptions", "保密例外", kind="textarea"), _field("liability", "违约责任", required=True, kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 保密信息", "披露方（甲方）：{discloser}\n接收方（乙方）：{recipient}\n保密信息范围：{confidential_info}\n允许使用目的：{purpose}"),
            TemplateSection("第二条 保密义务与期限", "乙方仅为约定目的使用保密信息，并采取合理保护措施。保密期限：{term}\n保密例外：{exceptions}"),
            TemplateSection("第三条 返还与违约", "返还、销毁与留存：{return_terms}\n违约责任：{liability}"),
        ),
    ),
    ContractTemplate(
        template_id="loan_contract",
        name="借款合同",
        category="资金往来",
        description="适用于个人或主体之间明确本金、期限、利率与还款安排的借款。",
        review_contract_type="general",
        source_kind="platform_structured_draft",
        publisher="RiskLens 合同中心",
        source_url=OFFICIAL_LIBRARY,
        source_note="利率、担保、资金用途与资金支付证据均应按实际交易和现行规则核对；大额或经营性借款建议律师复核。",
        fields=(
            _field("lender", "出借人", required=True), _field("borrower", "借款人", required=True),
            _field("principal", "借款本金（元）", required=True, kind="number"), _field("loan_date", "出借日期", required=True, kind="date"),
            _field("repayment_date", "到期还款日期", required=True, kind="date"), _field("interest", "年利率或利息约定", required=True),
            _field("payment_account", "支付与收款账户", required=True, kind="textarea"), _field("purpose", "借款用途", kind="textarea"),
            _field("guarantee", "担保约定", kind="textarea"), _field("default", "逾期与违约处理", required=True, kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 借款金额与支付", "出借人（甲方）：{lender}\n借款人（乙方）：{borrower}\n借款本金为人民币{principal}元，于{loan_date}支付。支付与收款账户：{payment_account}"),
            TemplateSection("第二条 期限、利息与用途", "借款到期日：{repayment_date}。利率或利息约定：{interest}。借款用途：{purpose}"),
            TemplateSection("第三条 担保与违约", "担保约定：{guarantee}\n逾期及违约处理：{default}"),
        ),
    ),
    ContractTemplate(
        template_id="business_cooperation_agreement",
        name="商务合作协议",
        category="委托与合作",
        description="适用于双方共同推进项目、约定分工、投入与收益安排。",
        review_contract_type="general",
        source_kind="platform_structured_draft",
        publisher="RiskLens 合同中心",
        source_url=OFFICIAL_LIBRARY,
        source_note="合作协议不当然构成合伙、劳动或代理关系；应明确项目主体、授权、税务、知识产权和退出机制。",
        fields=(
            _field("party_a", "合作方甲方", required=True), _field("party_b", "合作方乙方", required=True),
            _field("project", "合作项目", required=True, kind="textarea"), _field("division", "双方分工", required=True, kind="textarea"),
            _field("contribution", "投入与资源提供", required=True, kind="textarea"), _field("revenue", "收益或费用分配", required=True, kind="textarea"),
            _field("start_date", "开始日期", required=True, kind="date"), _field("end_date", "结束日期", required=True, kind="date"),
            _field("ip", "知识产权与数据归属", required=True, kind="textarea"), _field("exit", "退出与终止机制", required=True, kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 合作项目与分工", "合作方甲方：{party_a}\n合作方乙方：{party_b}\n合作项目：{project}\n双方分工：{division}"),
            TemplateSection("第二条 投入、期限与收益", "投入与资源：{contribution}\n合作期限自{start_date}起至{end_date}止。\n收益或费用分配：{revenue}"),
            TemplateSection("第三条 成果、保密与退出", "知识产权与数据归属：{ip}\n退出及终止机制：{exit}\n双方对未公开合作信息承担保密义务。"),
        ),
    ),
    ContractTemplate(
        template_id="equipment_lease_contract",
        name="设备租赁合同",
        category="居住与租赁",
        description="适用于机械、办公设备、器材等设备的有偿租赁。",
        review_contract_type="lease",
        source_kind="platform_structured_draft",
        publisher="RiskLens 合同中心",
        source_url=OFFICIAL_LIBRARY,
        source_note="设备的型号、状态、交付清单、维修责任、保险和损坏赔偿应结合实际设备逐项确认。",
        fields=(
            _field("lessor", "出租方", required=True), _field("lessee", "承租方", required=True),
            _field("equipment", "设备名称、型号与数量", required=True, kind="textarea"), _field("condition", "交付状态与附件清单", required=True, kind="textarea"),
            _field("start_date", "租赁开始日期", required=True, kind="date"), _field("end_date", "租赁结束日期", required=True, kind="date"),
            _field("rent", "租金金额（元）", required=True, kind="number"), _field("payment", "租金支付安排", required=True, kind="textarea"),
            _field("maintenance", "保管、维修与保险责任", required=True, kind="textarea"), _field("return_terms", "返还、损坏与赔偿规则", required=True, kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 租赁设备与交付", "出租方（甲方）：{lessor}\n承租方（乙方）：{lessee}\n租赁设备：{equipment}\n交付状态及附件：{condition}"),
            TemplateSection("第二条 租期、租金与使用", "租赁期限自{start_date}起至{end_date}止。租金为人民币{rent}元，支付安排：{payment}"),
            TemplateSection("第三条 保管、维修与返还", "保管、维修及保险：{maintenance}\n返还、损坏及赔偿：{return_terms}"),
        ),
    ),
    ContractTemplate(
        template_id="vehicle_sale_contract",
        name="二手车买卖合同",
        category="交易与采购",
        description="适用于二手乘用车交易，侧重车辆信息、价款、过户与交付。",
        review_contract_type="sale",
        source_kind="official_reference",
        publisher="国家市场监督管理总局合同示范文本库",
        source_url="https://htsfwb.samr.gov.cn/List?key=%E4%BA%8C%E6%89%8B%E8%BD%A6",
        source_note="参照二手车交易类示范文本结构；车辆状况、维修记录、权属、事故与抵押信息须以查验结果为准。",
        fields=(
            _field("seller", "出卖人", required=True), _field("buyer", "买受人", required=True),
            _field("vehicle", "车辆品牌、型号与车架号", required=True, kind="textarea"), _field("mileage", "表显里程与使用状况", required=True),
            _field("price", "成交价（元）", required=True, kind="number"), _field("payment", "付款安排", required=True, kind="textarea"),
            _field("ownership", "权属、抵押与事故披露", required=True, kind="textarea"), _field("transfer", "交付及过户安排", required=True, kind="textarea"),
            _field("warranty", "质量与售后约定", kind="textarea"), _field("default", "违约责任", required=True, kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 当事人与车辆", "出卖人（甲方）：{seller}\n买受人（乙方）：{buyer}\n车辆信息：{vehicle}\n表显里程及状况：{mileage}"),
            TemplateSection("第二条 价款、披露与过户", "成交价为人民币{price}元。付款安排：{payment}\n权属、抵押及事故披露：{ownership}\n交付及过户：{transfer}"),
            TemplateSection("第三条 质量与违约", "质量及售后：{warranty}\n违约责任：{default}"),
        ),
    ),
    ContractTemplate(
        template_id="renovation_contract",
        name="住宅装饰装修合同",
        category="居住与租赁",
        description="适用于住宅装修，覆盖施工范围、材料、工期、验收与保修。",
        review_contract_type="service",
        source_kind="platform_structured_draft",
        publisher="RiskLens 合同中心",
        source_url=OFFICIAL_LIBRARY,
        source_note="装修工程的图纸、报价单、材料品牌型号、增减项和验收单应作为附件逐项核对。",
        fields=(
            _field("owner", "发包方", required=True), _field("contractor", "承包方", required=True),
            _field("property_address", "施工地址", required=True), _field("scope", "施工范围与图纸依据", required=True, kind="textarea"),
            _field("materials", "材料品牌、规格与供应方式", required=True, kind="textarea"), _field("total_price", "工程总价（元）", required=True, kind="number"),
            _field("payment", "付款节点", required=True, kind="textarea"), _field("start_date", "开工日期", required=True, kind="date"),
            _field("end_date", "竣工日期", required=True, kind="date"), _field("acceptance", "验收、保修与增减项规则", required=True, kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 工程内容", "发包方（甲方）：{owner}\n承包方（乙方）：{contractor}\n施工地址：{property_address}\n施工范围及图纸：{scope}\n材料约定：{materials}"),
            TemplateSection("第二条 价款与工期", "工程总价为人民币{total_price}元。付款节点：{payment}\n工期自{start_date}起至{end_date}止。"),
            TemplateSection("第三条 验收、保修与变更", "验收、保修及增减项规则：{acceptance}"),
        ),
    ),
    ContractTemplate(
        template_id="technology_service_contract",
        name="技术服务合同",
        category="交易与采购",
        description="适用于软件开发、系统实施、技术咨询或技术支持等服务。",
        review_contract_type="service",
        source_kind="platform_structured_draft",
        publisher="RiskLens 合同中心",
        source_url=OFFICIAL_LIBRARY,
        source_note="技术成果、开源组件、数据安全、验收标准和知识产权归属存在较强个案性，应与项目附件一并复核。",
        fields=(
            _field("client", "委托方", required=True), _field("provider", "服务方", required=True),
            _field("scope", "服务或开发范围", required=True, kind="textarea"), _field("deliverables", "交付成果与验收标准", required=True, kind="textarea"),
            _field("start_date", "开始日期", required=True, kind="date"), _field("end_date", "结束日期", required=True, kind="date"),
            _field("fee", "合同金额（元）", required=True, kind="number"), _field("payment", "付款节点", required=True, kind="textarea"),
            _field("ip", "知识产权与开源合规约定", required=True, kind="textarea"), _field("data_security", "数据安全与保密安排", required=True, kind="textarea"),
        ),
        sections=(
            TemplateSection("第一条 服务范围与交付", "委托方（甲方）：{client}\n服务方（乙方）：{provider}\n服务范围：{scope}\n交付成果及验收：{deliverables}"),
            TemplateSection("第二条 期限、费用与支付", "服务期限自{start_date}起至{end_date}止。合同金额为人民币{fee}元，付款节点：{payment}"),
            TemplateSection("第三条 成果、数据与保密", "知识产权及开源合规：{ip}\n数据安全及保密：{data_security}"),
        ),
    ),
)


# 每个模板共享的“签署与争议”层。要求用户明确确认，而不是系统自行补造。
COMMON_CONFIRMATION_FIELDS: tuple[TemplateField, ...] = (
    _field("signing_date", "签订日期", required=True, kind="date"),
    _field("signing_place", "签订地点", required=True),
    _field("notice_address", "通知送达地址或电子邮箱", kind="textarea", placeholder="用于履约通知、催告和送达"),
    _field("dispute_resolution", "争议解决安排", required=True, kind="textarea", placeholder="协商、诉讼或仲裁的具体约定"),
    _field("supplementary_terms", "补充约定及附件清单", kind="textarea", placeholder="报价单、交接单、图纸、授权书等附件"),
)


# 对应交易的专属事实。至少一项为必填，确保草稿不会只停留在通用框架。
TEMPLATE_DETAIL_FIELDS: dict[str, tuple[TemplateField, ...]] = {
    "residential_lease": (
        _field("utilities", "水电燃气、物业及网络费用承担", required=True, kind="textarea"),
        _field("sublease_renewal", "转租、续租与优先承租约定", kind="textarea"),
    ),
    "labor_contract": (
        _field("rest_leave", "休息休假安排", required=True, kind="textarea"),
        _field("labor_protection", "劳动保护、劳动条件及职业危害防护", required=True, kind="textarea"),
        _field("rules_training", "规章制度、培训或服务期约定", kind="textarea"),
    ),
    "labor_service_contract": (
        _field("relationship_boundary", "双方关系及管理边界", required=True, kind="textarea", placeholder="明确独立劳务安排和日常管理边界"),
        _field("tax_expense", "税费与履约费用承担", required=True, kind="textarea"),
        _field("termination", "提前终止与结算规则", kind="textarea"),
    ),
    "goods_sale_contract": (
        _field("invoice", "发票类型、税率及开具时间", required=True, kind="textarea"),
        _field("risk_transfer", "运输、风险转移与所有权保留", required=True, kind="textarea"),
        _field("return_terms", "退换货及不合格品处理", kind="textarea"),
    ),
    "service_contract": (
        _field("change_process", "服务范围变更与确认流程", required=True, kind="textarea"),
        _field("service_breach", "服务不达标、延迟和违约处理", required=True, kind="textarea"),
        _field("personnel", "项目人员与替换要求", kind="textarea"),
    ),
    "entrustment_contract": (
        _field("expense", "履行费用、垫付与报销规则", required=True, kind="textarea"),
        _field("instructions", "指示、变更和紧急事项处理", required=True, kind="textarea"),
        _field("return_materials", "资料、成果及印章返还", kind="textarea"),
    ),
    "confidentiality_agreement": (
        _field("security_measures", "信息安全保护措施", required=True, kind="textarea"),
        _field("permitted_recipients", "允许接触信息的人员或第三方", required=True, kind="textarea"),
        _field("emergency_notice", "泄露事件通知与补救", kind="textarea"),
    ),
    "loan_contract": (
        _field("repayment_schedule", "还款计划与还款账户", required=True, kind="textarea"),
        _field("transfer_evidence", "放款凭证与资金交付确认", required=True, kind="textarea"),
        _field("prepayment", "提前还款或展期规则", kind="textarea"),
    ),
    "business_cooperation_agreement": (
        _field("governance", "项目决策、授权与沟通机制", required=True, kind="textarea"),
        _field("expense_settlement", "共同费用、税务及结算规则", required=True, kind="textarea"),
        _field("non_compete", "排他、竞业或客户保护约定", kind="textarea"),
    ),
    "equipment_lease_contract": (
        _field("operation_rules", "设备操作资质、使用限制与培训", required=True, kind="textarea"),
        _field("inspection", "交接、巡检与故障报告流程", required=True, kind="textarea"),
    ),
    "vehicle_sale_contract": (
        _field("inspection", "验车、试驾及车辆状况确认", required=True, kind="textarea"),
        _field("documents", "随车证照、钥匙及资料交接", required=True, kind="textarea"),
    ),
    "renovation_contract": (
        _field("change_orders", "工程变更、增减项与报价确认", required=True, kind="textarea"),
        _field("site_safety", "施工现场安全、成品保护与邻里协调", required=True, kind="textarea"),
    ),
    "technology_service_contract": (
        _field("change_control", "需求变更、版本控制与确认流程", required=True, kind="textarea"),
        _field("support_warranty", "上线支持、缺陷修复与质保安排", required=True, kind="textarea"),
    ),
}


TEMPLATE_DETAIL_SECTIONS: dict[str, TemplateSection] = {
    "residential_lease": TemplateSection("第四条 费用、转租与续租", "费用承担：{utilities}\n转租、续租及优先承租：{sublease_renewal}"),
    "labor_contract": TemplateSection("第五条 休息休假、劳动保护及培训", "休息休假：{rest_leave}\n劳动保护及劳动条件：{labor_protection}\n规章制度、培训或服务期：{rules_training}"),
    "labor_service_contract": TemplateSection("第四条 关系边界、税费与终止", "关系及管理边界：{relationship_boundary}\n税费及履约费用：{tax_expense}\n提前终止与结算：{termination}"),
    "goods_sale_contract": TemplateSection("第四条 税务、风险与退换货", "发票及税务：{invoice}\n运输、风险转移及所有权：{risk_transfer}\n退换货及不合格品处理：{return_terms}"),
    "service_contract": TemplateSection("第四条 变更、人员与违约", "范围变更流程：{change_process}\n项目人员：{personnel}\n服务不达标、延迟及违约：{service_breach}"),
    "entrustment_contract": TemplateSection("第四条 费用、指示与资料返还", "履行费用及报销：{expense}\n指示、变更和紧急事项：{instructions}\n资料、成果及印章返还：{return_materials}"),
    "confidentiality_agreement": TemplateSection("第四条 安全措施与事件处置", "信息安全措施：{security_measures}\n允许接触人员或第三方：{permitted_recipients}\n泄露事件通知与补救：{emergency_notice}"),
    "loan_contract": TemplateSection("第四条 还款、凭证与展期", "还款计划及账户：{repayment_schedule}\n放款凭证及交付确认：{transfer_evidence}\n提前还款或展期：{prepayment}"),
    "business_cooperation_agreement": TemplateSection("第四条 决策、费用与保护安排", "项目决策及授权：{governance}\n共同费用、税务及结算：{expense_settlement}\n排他、竞业或客户保护：{non_compete}"),
    "equipment_lease_contract": TemplateSection("第四条 操作、巡检与故障", "操作资质、使用限制及培训：{operation_rules}\n交接、巡检及故障报告：{inspection}"),
    "vehicle_sale_contract": TemplateSection("第四条 验车与资料交接", "验车、试驾及车辆状况确认：{inspection}\n证照、钥匙及随车资料：{documents}"),
    "renovation_contract": TemplateSection("第四条 工程变更与现场管理", "工程变更及增减项：{change_orders}\n施工安全、成品保护及邻里协调：{site_safety}"),
    "technology_service_contract": TemplateSection("第四条 变更、支持与质保", "需求变更及版本控制：{change_control}\n上线支持、缺陷修复及质保：{support_warranty}"),
}


TEMPLATE_REVIEW_CHECKPOINTS: dict[str, tuple[str, ...]] = {
    "residential_lease": ("房屋权属与交付清单", "租金、押金及费用承担", "维修、转租与提前解除", "争议解决和通知送达"),
    "labor_contract": ("劳动合同法必备条款", "工时、工资、社保与休假", "试用期及竞业限制边界", "劳动保护与解除终止"),
    "labor_service_contract": ("劳动关系与劳务关系边界", "服务确认与报酬结算", "税费、安全及责任承担", "提前终止和资料返还"),
    "goods_sale_contract": ("标的、质量和验收标准", "价款、发票和交付", "风险转移与所有权", "售后、退换货和违约"),
    "service_contract": ("服务范围、标准和验收", "费用与变更控制", "人员、数据与成果归属", "不达标和延迟处理"),
    "entrustment_contract": ("委托事项和授权边界", "费用、报告和资料交付", "转委托与紧急事项", "解除、结算和返还"),
    "confidentiality_agreement": ("保密信息范围和用途", "接触人员与安全措施", "返还、销毁和例外", "泄露处置与违约责任"),
    "loan_contract": ("资金交付证据与还款计划", "利息、费用和担保", "提前还款、展期和逾期", "主体资格及适用规则"),
    "business_cooperation_agreement": ("项目分工、授权和投入", "费用、税务和收益结算", "成果、数据和保密", "退出、终止和责任"),
    "equipment_lease_contract": ("设备清单、状态和交接", "操作资格、保管和保险", "维修、故障和损坏赔偿", "返还、验收和费用结算"),
    "vehicle_sale_contract": ("车辆权属、事故和抵押披露", "验车、里程和质量约定", "价款、过户和资料交接", "售后与违约责任"),
    "renovation_contract": ("图纸、材料和报价附件", "工期、付款和工程变更", "施工安全和验收保修", "增减项、停工和结算"),
    "technology_service_contract": ("需求、交付和验收标准", "变更控制和项目协作", "知识产权、数据与开源合规", "支持、质保和违约责任"),
}


class ContractTemplateService:
    """提供模板目录、结构化完整度和不补造事实的草稿。"""

    def __init__(self) -> None:
        self._by_id = {template.template_id: template for template in TEMPLATES}

    def list_templates(self) -> list[dict[str, Any]]:
        return [self.public_template(template) for template in TEMPLATES]

    def get_template(self, template_id: str) -> ContractTemplate:
        try:
            return self._by_id[template_id]
        except KeyError as exc:
            raise ValueError("未找到该合同模板") from exc

    @staticmethod
    def _fields(template: ContractTemplate) -> tuple[TemplateField, ...]:
        """合并基础字段、场景字段和统一确认字段，保持字段名唯一。"""
        fields = (*template.fields, *TEMPLATE_DETAIL_FIELDS.get(template.template_id, ()), *COMMON_CONFIRMATION_FIELDS)
        seen: set[str] = set()
        return tuple(field for field in fields if not (field.key in seen or seen.add(field.key)))

    @staticmethod
    def _sections(template: ContractTemplate) -> tuple[TemplateSection, ...]:
        detail = TEMPLATE_DETAIL_SECTIONS.get(template.template_id)
        standard = TemplateSection(
            "签署、通知与争议处理",
            "签订日期：{signing_date}；签订地点：{signing_place}。\n通知送达地址或电子邮箱：{notice_address}\n争议解决安排：{dispute_resolution}\n补充约定及附件：{supplementary_terms}",
        )
        return (*template.sections, *((detail,) if detail else ()), standard)

    def public_template(self, template: ContractTemplate) -> dict[str, Any]:
        fields = self._fields(template)
        return {
            "id": template.template_id,
            "name": template.name,
            "category": template.category,
            "description": template.description,
            "review_contract_type": template.review_contract_type,
            "source_kind": template.source_kind,
            "publisher": template.publisher,
            "source_url": template.source_url,
            "source_note": template.source_note,
            "review_checkpoints": list(TEMPLATE_REVIEW_CHECKPOINTS.get(template.template_id, ())),
            "fields": [
                {
                    "key": field.key,
                    "label": field.label,
                    "kind": field.kind,
                    "required": field.required,
                    "placeholder": field.placeholder,
                    "options": list(field.options),
                }
                for field in fields
            ],
        }

    def analyze(self, template_id: str, facts: dict[str, str]) -> dict[str, Any]:
        template = self.get_template(template_id)
        fields = self._fields(template)
        normalized = self._normalize_facts(template, facts)
        missing = [field for field in fields if field.required and not normalized.get(field.key)]
        return {
            "template": self.public_template(template),
            "facts": normalized,
            "required_total": sum(field.required for field in fields),
            "required_complete": sum(bool(normalized.get(field.key)) for field in fields if field.required),
            "missing": [{"key": field.key, "label": field.label} for field in missing],
            "can_generate": not missing,
            "notice": "系统只使用表单中明确填写的内容；不会从描述中推断姓名、金额、日期或法律事实。",
        }

    def build_draft(self, template_id: str, facts: dict[str, str], allow_placeholders: bool = False) -> dict[str, Any]:
        template = self.get_template(template_id)
        analysis = self.analyze(template_id, facts)
        missing = analysis["missing"]
        if missing and not allow_placeholders:
            return {"status": "needs_clarification", **analysis}

        values = dict(analysis["facts"])
        labels = {field.key: field.label for field in self._fields(template)}
        for key, label in labels.items():
            values.setdefault(key, f"【待确认：{label}】")
        sections = [{"title": section.title, "text": section.body.format_map(values)} for section in self._sections(template)]
        rendered = "\n\n".join(f"{section['title']}\n{section['text']}" for section in sections)
        other_clause = "本合同未尽事宜由双方协商处理；本合同附件、补充协议与本合同具有同等效力。"
        rendered = f"{template.name}（可编辑草稿）\n\n{rendered}\n\n第{len(sections) + 1}条 其他\n{other_clause}\n\n---\n本草稿仅供事实确认和条款整理，不构成律师法律意见或签署建议。"
        return {
            "status": "draft_ready",
            **analysis,
            "sections": sections,
            "rendered_contract": rendered,
            "template_reference": {
                "source_kind": template.source_kind,
                "publisher": template.publisher,
                "source_url": template.source_url,
                "notice": template.source_note,
            },
        }

    @staticmethod
    def _normalize_facts(template: ContractTemplate, facts: dict[str, str]) -> dict[str, str]:
        allowed = {field.key for field in ContractTemplateService._fields(template)}
        normalized: dict[str, str] = {}
        for key, value in facts.items():
            if key not in allowed or not isinstance(value, str):
                continue
            clean = value.strip()
            if clean:
                normalized[key] = clean[:4000]
        return normalized


contract_template_service = ContractTemplateService()
