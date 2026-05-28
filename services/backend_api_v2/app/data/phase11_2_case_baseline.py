PHASE11_2_CASE_BASELINE = [
    {"case_id":"ai_training_dataset_trade","final_score":81.0,"programmatic_score":87.0,"llm_score":73.0,"grade":"B","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"专门证据有限，部分 claim 只有部分支持。"},
    {"case_id":"anonymization_reidentification_boundary","final_score":60.0,"programmatic_score":83.0,"llm_score":48.0,"grade":"D","ge_70":False,"bge_m3_status":"effective","main_issue":"事实摘要占位符多，匿名化边界规则和专门证据不足。"},
    {"case_id":"cloud_saas_remote_access","final_score":39.0,"programmatic_score":43.0,"llm_score":34.0,"grade":"F","ge_70":False,"bge_m3_status":"partially_effective","main_issue":"缺核心法律条款，过度依赖技术标准，专业证据严重不足。"},
    {"case_id":"connected_vehicle_overseas_algorithm","final_score":58.0,"programmatic_score":67.0,"llm_score":45.0,"grade":"D","ge_70":False,"bge_m3_status":"partially_effective","main_issue":"车联网/重要数据/境外算法访问证据不足，事实具体性低。"},
    {"case_id":"crossborder_ecommerce_ads","final_score":79.0,"programmatic_score":88.0,"llm_score":65.0,"grade":"B","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"事实细节不足，部分 claim 依赖背景支持。"},
    {"case_id":"crossborder_hr_group_transfer","final_score":78.0,"programmatic_score":88.0,"llm_score":64.0,"grade":"B","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"跨境 HR 专门规则覆盖不足，部分支持为背景或限制性说明。"},
    {"case_id":"ecommerce_profile","final_score":83.0,"programmatic_score":92.0,"llm_score":70.0,"grade":"B","ge_70":True,"bge_m3_status":"effective","main_issue":"业务事实多为待核实，行业专门证据不足。"},
    {"case_id":"enterprise_data_flow","final_score":49.0,"programmatic_score":43.0,"llm_score":58.0,"grade":"F","ge_70":False,"bge_m3_status":"partially_effective","main_issue":"核心法律证据缺失，仅技术标准无法支撑纯法律结论。"},
    {"case_id":"finance_trade","final_score":50.0,"programmatic_score":50.0,"llm_score":70.0,"grade":"D","ge_70":False,"bge_m3_status":"partially_effective","main_issue":"LLM 阅读较强，但 programmatic support cap 主导。"},
    {"case_id":"lowrisk_anonymous_stats","final_score":60.0,"programmatic_score":84.0,"llm_score":24.0,"grade":"D","ge_70":False,"bge_m3_status":"effective","main_issue":"事实和法律规则具体性低，技术标准不能直接支撑法律结论。"},
    {"case_id":"medical_crossborder","final_score":80.0,"programmatic_score":88.0,"llm_score":67.0,"grade":"B","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"医疗健康专门证据不足，核心事实仍待核实。"},
    {"case_id":"mixed_crossborder_auto","final_score":80.0,"programmatic_score":88.0,"llm_score":68.0,"grade":"B","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"汽车、保险、算法等场景专门证据仍不足。"},
    {"case_id":"outsourced_data_processing","final_score":50.0,"programmatic_score":50.0,"llm_score":52.0,"grade":"D","ge_70":False,"bge_m3_status":"effective","main_issue":"委托处理合同、安全措施等专门证据不足，programmatic cap 仍有效。"},
    {"case_id":"platform_merchant_data_access","final_score":72.0,"programmatic_score":72.0,"llm_score":72.0,"grade":"C","ge_70":True,"bge_m3_status":"effective","main_issue":"缺平台商户数据访问专门规则，证据与商户权益 claim 匹配度有限。"},
    {"case_id":"public_data_product_listing","final_score":77.0,"programmatic_score":91.0,"llm_score":55.0,"grade":"B","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"较重依赖单一规则，个人信息和证据缺口 claim 匹配度弱。"},
    {"case_id":"sensitive_pi_biometric_processing","final_score":50.0,"programmatic_score":50.0,"llm_score":75.0,"grade":"D","ge_70":False,"bge_m3_status":"effective","main_issue":"LLM 高但 programmatic cap 压分，缺具体业务底稿与强证据。"},
    {"case_id":"supplier_data_sharing","final_score":70.0,"programmatic_score":72.0,"llm_score":67.0,"grade":"C","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"第三方接收方、合同、安全措施等专门证据不足。"},
    {"case_id":"third_party_data_broker_trade","final_score":81.0,"programmatic_score":92.0,"llm_score":64.0,"grade":"B","ge_70":True,"bge_m3_status":"partially_effective","main_issue":"法律规则精确性不足，证据与 claim 多为部分支持。"},
]

CASE_IDS = [row["case_id"] for row in PHASE11_2_CASE_BASELINE]
