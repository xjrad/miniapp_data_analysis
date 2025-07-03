# utils/__init__.py
# 🛠️ 工具模块初始化文件

from .data_processor import (
    format_event_name,
    clean_page_path,
    extract_domain_from_url,
    categorize_referrer,
    get_time_condition,
    extract_json_property,
    build_comprehensive_step_identifier,
    apply_path_length_filter,
    preprocess_dataframe,
    generate_mock_trend_data,
    generate_mock_hourly_data
)

from .path_analyzer import (
    extract_option_key,
    build_enhanced_user_paths,
    calculate_step_positions,
    build_enhanced_sankey_data,
    analyze_step_distribution,
    analyze_path_conversion,
    calculate_enhanced_path_stats,
    build_session_paths,
    get_popular_paths,
    calculate_path_metrics
)

__all__ = [
    # data_processor
    'format_event_name',
    'clean_page_path',
    'extract_domain_from_url',
    'categorize_referrer',
    'get_time_condition',
    'extract_json_property',
    'build_comprehensive_step_identifier',
    'apply_path_length_filter',
    'preprocess_dataframe',
    'generate_mock_trend_data',
    'generate_mock_hourly_data',
    
    # path_analyzer
    'extract_option_key',
    'build_enhanced_user_paths',
    'calculate_step_positions',
    'build_enhanced_sankey_data',
    'analyze_step_distribution',
    'analyze_path_conversion',
    'calculate_enhanced_path_stats',
    'build_session_paths',
    'get_popular_paths',
    'calculate_path_metrics'
]