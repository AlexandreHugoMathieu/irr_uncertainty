config
======

.. automodule:: pv_uncertainty.config



data.degradation_db
===================

.. automodule:: pv_uncertainty.data.degradation_db

.. autofunction:: pv_uncertainty.data.degradation_db.get_ageing
.. autofunction:: pv_uncertainty.data.degradation_db.get_degradation_data
.. autofunction:: pv_uncertainty.data.degradation_db.get_degradation_data_lit


data.merra2_api
===============

.. automodule:: pv_uncertainty.data.merra2_api

.. autofunction:: pv_uncertainty.data.merra2_api.drop_nc4_merra_data
.. autofunction:: pv_uncertainty.data.merra2_api.get_merra_http_data
.. autofunction:: pv_uncertainty.data.merra2_api.merra2_wait_job_processed
.. autofunction:: pv_uncertainty.data.merra2_api.prepare_merra_job


data.pm_data
============

.. automodule:: pv_uncertainty.data.pm_data

.. autofunction:: pv_uncertainty.data.pm_data.find_nearest_idx
.. autofunction:: pv_uncertainty.data.pm_data.get_pm_data_datagouv
.. autofunction:: pv_uncertainty.data.pm_data.merra2_pm
.. autofunction:: pv_uncertainty.data.pm_data.merra2_pm10
.. autofunction:: pv_uncertainty.data.pm_data.merra2_pm25
.. autofunction:: pv_uncertainty.data.pm_data.merra2_pm_pkl
.. autofunction:: pv_uncertainty.data.pm_data.merra2_unit_site_id


data.pv_data_db
===============

.. automodule:: pv_uncertainty.data.pv_data_db

.. autofunction:: pv_uncertainty.data.pv_data_db.create_connection
.. autofunction:: pv_uncertainty.data.pv_data_db.daily_check_db
.. autofunction:: pv_uncertainty.data.pv_data_db.drop_table
.. autofunction:: pv_uncertainty.data.pv_data_db.get_all_table_names
.. autofunction:: pv_uncertainty.data.pv_data_db.get_charac_from_table_name
.. autofunction:: pv_uncertainty.data.pv_data_db.get_table_name_from_charac
.. autofunction:: pv_uncertainty.data.pv_data_db.insert_data
.. autofunction:: pv_uncertainty.data.pv_data_db.push_ts_db
.. autofunction:: pv_uncertainty.data.pv_data_db.pv_data_create_data_table
.. autofunction:: pv_uncertainty.data.pv_data_db.read_db_ts
.. autofunction:: pv_uncertainty.data.pv_data_db.read_db_ts_multiple
.. autofunction:: pv_uncertainty.data.pv_data_db.read_db_ts_table
.. autofunction:: pv_uncertainty.data.pv_data_db.update_data


data.shadow_mask
================

.. automodule:: pv_uncertainty.data.shadow_mask

.. autofunction:: pv_uncertainty.data.shadow_mask.figure_shadow_mask
.. autofunction:: pv_uncertainty.data.shadow_mask.get_mask_csv
.. autofunction:: pv_uncertainty.data.shadow_mask.pvgis_mask


data.six_installations
======================

.. automodule:: pv_uncertainty.data.six_installations

.. autofunction:: pv_uncertainty.data.six_installations.install_meta_data


data.soiling_data
=================

.. automodule:: pv_uncertainty.data.soiling_data

.. autofunction:: pv_uncertainty.data.soiling_data.get_ts_soiling
.. autofunction:: pv_uncertainty.data.soiling_data.soiling_site_meta_data
.. autofunction:: pv_uncertainty.data.soiling_data.soiling_sr_site


data.solar_data
===============

.. automodule:: pv_uncertainty.data.solar_data

.. autofunction:: pv_uncertainty.data.solar_data.bsrn_lat_long_alt
.. autofunction:: pv_uncertainty.data.solar_data.bsrn_name
.. autofunction:: pv_uncertainty.data.solar_data.get_filter_v2
.. autofunction:: pv_uncertainty.data.solar_data.get_solar_position_1m
.. autofunction:: pv_uncertainty.data.solar_data.ghi_h_extra
.. autofunction:: pv_uncertainty.data.solar_data.pvlive_lat_long_alt
.. autofunction:: pv_uncertainty.data.solar_data.solarpos
.. autofunction:: pv_uncertainty.data.solar_data.stations_meta
.. autofunction:: pv_uncertainty.data.solar_data.stations_pv_live


data.weather_data
=================

.. automodule:: pv_uncertainty.data.weather_data

.. autofunction:: pv_uncertainty.data.weather_data.get_pvlive
.. autofunction:: pv_uncertainty.data.weather_data.get_weather_proj
.. autofunction:: pv_uncertainty.data.weather_data.helioclim_city_API
.. autofunction:: pv_uncertainty.data.weather_data.helioclim_csv_download
.. autofunction:: pv_uncertainty.data.weather_data.helioclim_treatment
.. autofunction:: pv_uncertainty.data.weather_data.login_heliocity_v2_API
.. autofunction:: pv_uncertainty.data.weather_data.process_bsrn
.. autofunction:: pv_uncertainty.data.weather_data.search_similar_local_data
.. autofunction:: pv_uncertainty.data.weather_data.weather_tmy_futur


installation_analysis.ademe_projection_v2_2024
==============================================

.. automodule:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024

.. autofunction:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024.ademe_actuals
.. autofunction:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024.ademe_masks_2024
.. autofunction:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024.ademe_spe_data
.. autofunction:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024.doe_ts
.. autofunction:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024.get_ademe_base_args
.. autofunction:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024.get_ademe_masks
.. autofunction:: pv_uncertainty.installation_analysis.ademe_projection_v2_2024.weather_monthly_ademe_doe


installation_analysis.arkema_projection_v2_2024
===============================================

.. automodule:: pv_uncertainty.installation_analysis.arkema_projection_v2_2024

.. autofunction:: pv_uncertainty.installation_analysis.arkema_projection_v2_2024.arkema_masks
.. autofunction:: pv_uncertainty.installation_analysis.arkema_projection_v2_2024.arkema_spe_data
.. autofunction:: pv_uncertainty.installation_analysis.arkema_projection_v2_2024.get_base_args


installation_analysis.bacalu_projection_v2_2024
===============================================

.. automodule:: pv_uncertainty.installation_analysis.bacalu_projection_v2_2024

.. autofunction:: pv_uncertainty.installation_analysis.bacalu_projection_v2_2024.bacalu_masks
.. autofunction:: pv_uncertainty.installation_analysis.bacalu_projection_v2_2024.bacalu_spe_data
.. autofunction:: pv_uncertainty.installation_analysis.bacalu_projection_v2_2024.get_base_args


installation_analysis.cigs_projection_v2_2024
=============================================

.. automodule:: pv_uncertainty.installation_analysis.cigs_projection_v2_2024

.. autofunction:: pv_uncertainty.installation_analysis.cigs_projection_v2_2024.cigs_masks_2024
.. autofunction:: pv_uncertainty.installation_analysis.cigs_projection_v2_2024.cigs_spe_data
.. autofunction:: pv_uncertainty.installation_analysis.cigs_projection_v2_2024.get_cigs_masks


kpi.loss_calculator
===================

.. automodule:: pv_uncertainty.kpi.loss_calculator

.. autofunction:: pv_uncertainty.kpi.loss_calculator.get_pvloss


kpi.performance
===============

.. automodule:: pv_uncertainty.kpi.performance

.. autofunction:: pv_uncertainty.kpi.performance.pr


models.inverter
===============

.. automodule:: pv_uncertainty.models.inverter

.. autofunction:: pv_uncertainty.models.inverter.pvwatts_AM


models.inverter_derating
========================

.. automodule:: pv_uncertainty.models.inverter_derating

.. autofunction:: pv_uncertainty.models.inverter_derating.generate_t_derating
.. autofunction:: pv_uncertainty.models.inverter_derating.sma_derating_info
.. autofunction:: pv_uncertainty.models.inverter_derating.solaredge_derating_data
.. autofunction:: pv_uncertainty.models.inverter_derating.temp_derating


models.irr_limits
=================

.. automodule:: pv_uncertainty.models.irr_limits

.. autofunction:: pv_uncertainty.models.irr_limits.get_irr_limits
.. autofunction:: pv_uncertainty.models.irr_limits.get_poa_limits


models.iv_curve_failure
=======================

.. automodule:: pv_uncertainty.models.iv_curve_failure

.. autofunction:: pv_uncertainty.models.iv_curve_failure.bp_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.cc_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.ci_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.cor_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.failure_bools
.. autofunction:: pv_uncertainty.models.iv_curve_failure.failure_prep
.. autofunction:: pv_uncertainty.models.iv_curve_failure.gb_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_bp_sc_bool
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_failure_bool
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_failure_cellstrg_bool
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_fault
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_list_module_layout
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_meta_cellstrg_index
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_meta_index
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_meta_str_index
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_open_circuit
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_shad_list
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_vi_bp
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_vi_cc
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_vi_cor
.. autofunction:: pv_uncertainty.models.iv_curve_failure.get_vi_cor_v2
.. autofunction:: pv_uncertainty.models.iv_curve_failure.irr_strg_hete
.. autofunction:: pv_uncertainty.models.iv_curve_failure.iv_agg_failure
.. autofunction:: pv_uncertainty.models.iv_curve_failure.jbox_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.location_pd_to_nstring
.. autofunction:: pv_uncertainty.models.iv_curve_failure.location_to_nstring
.. autofunction:: pv_uncertainty.models.iv_curve_failure.pdac_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.pddc_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.wirac_indexes
.. autofunction:: pv_uncertainty.models.iv_curve_failure.wirdc_indexes


models.optic_model
==================

.. automodule:: pv_uncertainty.models.optic_model

.. autofunction:: pv_uncertainty.models.optic_model.apply_diffuse
.. autofunction:: pv_uncertainty.models.optic_model.apply_erbs
.. autofunction:: pv_uncertainty.models.optic_model.apply_hay_davies
.. autofunction:: pv_uncertainty.models.optic_model.apply_hay_davies_withmask
.. autofunction:: pv_uncertainty.models.optic_model.erbs_AM
.. autofunction:: pv_uncertainty.models.optic_model.erbs_simple
.. autofunction:: pv_uncertainty.models.optic_model.get_poa_desthieux
.. autofunction:: pv_uncertainty.models.optic_model.haydavies_desthieux
.. autofunction:: pv_uncertainty.models.optic_model.shading_factor_ts
.. autofunction:: pv_uncertainty.models.optic_model.shading_loss_pdc
.. autofunction:: pv_uncertainty.models.optic_model.svf_desthieux


models.pv_system
================

.. automodule:: pv_uncertainty.models.pv_system

.. autofunction:: pv_uncertainty.models.pv_system.col_name_management
.. autofunction:: pv_uncertainty.models.pv_system.compute_irr_eff_cols
.. autofunction:: pv_uncertainty.models.pv_system.eff_irr_computation
.. autofunction:: pv_uncertainty.models.pv_system.get_config
.. autofunction:: pv_uncertainty.models.pv_system.inject_agg_data
.. autofunction:: pv_uncertainty.models.pv_system.iv_aggregation_system
.. autofunction:: pv_uncertainty.models.pv_system.iv_store
.. autofunction:: pv_uncertainty.models.pv_system.layout_same
.. autofunction:: pv_uncertainty.models.pv_system.pkl_pv_management
.. autofunction:: pv_uncertainty.models.pv_system.power_model_module
.. autofunction:: pv_uncertainty.models.pv_system.prep_inputs
.. autofunction:: pv_uncertainty.models.pv_system.prepare_column_aggreg
.. autofunction:: pv_uncertainty.models.pv_system.pv_model
.. autofunction:: pv_uncertainty.models.pv_system.pv_model_module
.. autofunction:: pv_uncertainty.models.pv_system.string_agg
.. autofunction:: pv_uncertainty.models.pv_system.string_layout


models.pv_system_uncertainty
============================

.. automodule:: pv_uncertainty.models.pv_system_uncertainty

.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.combine_summaries
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.combine_summaries_d
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.fill_dict
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.general_uncertainties
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.generate_summaries
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.get_summary_df
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.inv_uncertainties
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.projection_uncertainty
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.projection_uncertainty_wfailures
.. autofunction:: pv_uncertainty.models.pv_system_uncertainty.projection_uncertainty_wfailures_comparison


publications.pv_uncertainty_2024_article
========================================

.. automodule:: pv_uncertainty.publications.pv_uncertainty_2024_article

.. autofunction:: pv_uncertainty.publications.pv_uncertainty_2024_article.calculate_kt_kpis
.. autofunction:: pv_uncertainty.publications.pv_uncertainty_2024_article.plot_kt_kt


publications.pv_uncertainty_2024_poster
=======================================

.. automodule:: pv_uncertainty.publications.pv_uncertainty_2024_poster

.. autofunction:: pv_uncertainty.publications.pv_uncertainty_2024_poster.collect_quantiles_pv_live
.. autofunction:: pv_uncertainty.publications.pv_uncertainty_2024_poster.download_pvgis_irr_2015
.. autofunction:: pv_uncertainty.publications.pv_uncertainty_2024_poster.ghi_dhi_bhi_pvigs_2015


uncertainty.study_aging
=======================

.. automodule:: pv_uncertainty.uncertainty.study_aging

.. autofunction:: pv_uncertainty.uncertainty.study_aging.aging_sample
.. autofunction:: pv_uncertainty.uncertainty.study_aging.aging_scenarios


uncertainty.study_dc_loss
=========================

.. automodule:: pv_uncertainty.uncertainty.study_dc_loss

.. autofunction:: pv_uncertainty.uncertainty.study_dc_loss.dc_loss_scenarios


uncertainty.study_humidity
==========================

.. automodule:: pv_uncertainty.uncertainty.study_humidity

.. autofunction:: pv_uncertainty.uncertainty.study_humidity.humidity_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_humidity.humidity_scenarios2


uncertainty.study_iam
=====================

.. automodule:: pv_uncertainty.uncertainty.study_iam

.. autofunction:: pv_uncertainty.uncertainty.study_iam.calculate_iam
.. autofunction:: pv_uncertainty.uncertainty.study_iam.calculate_iam_diffus_error
.. autofunction:: pv_uncertainty.uncertainty.study_iam.calculate_iamd_ani
.. autofunction:: pv_uncertainty.uncertainty.study_iam.fit_predict
.. autofunction:: pv_uncertainty.uncertainty.study_iam.get_iam_diff
.. autofunction:: pv_uncertainty.uncertainty.study_iam.get_iam_global
.. autofunction:: pv_uncertainty.uncertainty.study_iam.get_pvgis_data
.. autofunction:: pv_uncertainty.uncertainty.study_iam.iam_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_iam.iam_scenarios_v2


uncertainty.study_inverter
==========================

.. automodule:: pv_uncertainty.uncertainty.study_inverter

.. autofunction:: pv_uncertainty.uncertainty.study_inverter.generate_inv_scenarios_v2


uncertainty.study_irradiance
============================

.. automodule:: pv_uncertainty.uncertainty.study_irradiance

.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.add_transpo_error
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.bar_poster
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.bestdistfit
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.collect_quantiles
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.dist_transfo
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.generate_transpo_error
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.get_kd_dist_v2
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.irr_scenarios_v4
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.irrh_scenarios_v4
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.poa_limit_adj
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.poly_func
.. autofunction:: pv_uncertainty.uncertainty.study_irradiance.transpo_scenarios_v4


uncertainty.study_orientation
=============================

.. automodule:: pv_uncertainty.uncertainty.study_orientation

.. autofunction:: pv_uncertainty.uncertainty.study_orientation.gaussian_plots
.. autofunction:: pv_uncertainty.uncertainty.study_orientation.generate_guaussian_error_tilt_azimuth
.. autofunction:: pv_uncertainty.uncertainty.study_orientation.get_gaussian_orientation_std
.. autofunction:: pv_uncertainty.uncertainty.study_orientation.orientation_data
.. autofunction:: pv_uncertainty.uncertainty.study_orientation.orientation_scenarios_v2


uncertainty.study_power
=======================

.. automodule:: pv_uncertainty.uncertainty.study_power

.. autofunction:: pv_uncertainty.uncertainty.study_power.power_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_power.power_scenarios_random_biais


uncertainty.study_power_tol
===========================

.. automodule:: pv_uncertainty.uncertainty.study_power_tol

.. autofunction:: pv_uncertainty.uncertainty.study_power_tol.power_tolerance_scenarios


uncertainty.study_shading
=========================

.. automodule:: pv_uncertainty.uncertainty.study_shading

.. autofunction:: pv_uncertainty.uncertainty.study_shading.generate_shadings
.. autofunction:: pv_uncertainty.uncertainty.study_shading.get_ts_masks_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_shading.shading_lambda_halfcauchy
.. autofunction:: pv_uncertainty.uncertainty.study_shading.shading_scenarios_unknown
.. autofunction:: pv_uncertainty.uncertainty.study_shading.shading_scenarios_v3
.. autofunction:: pv_uncertainty.uncertainty.study_shading.shading_suneye_scenarios_v3


uncertainty.study_smm
=====================

.. automodule:: pv_uncertainty.uncertainty.study_smm

.. autofunction:: pv_uncertainty.uncertainty.study_smm.calculate_smm
.. autofunction:: pv_uncertainty.uncertainty.study_smm.smm_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_smm.smm_scenarios2
.. autofunction:: pv_uncertainty.uncertainty.study_smm.smm_scenarios3
.. autofunction:: pv_uncertainty.uncertainty.study_smm.smm_scenarios3_wtascns


uncertainty.study_snow
======================

.. automodule:: pv_uncertainty.uncertainty.study_snow

.. autofunction:: pv_uncertainty.uncertainty.study_snow.compute_monthly_energy_loss
.. autofunction:: pv_uncertainty.uncertainty.study_snow.generate_snow_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_snow.random_ts
.. autofunction:: pv_uncertainty.uncertainty.study_snow.snow_error_data
.. autofunction:: pv_uncertainty.uncertainty.study_snow.snow_loss_model
.. autofunction:: pv_uncertainty.uncertainty.study_snow.snow_monthly_error
.. autofunction:: pv_uncertainty.uncertainty.study_snow.snow_scenarios


uncertainty.study_soiling
=========================

.. automodule:: pv_uncertainty.uncertainty.study_soiling

.. autofunction:: pv_uncertainty.uncertainty.study_soiling.find_7days
.. autofunction:: pv_uncertainty.uncertainty.study_soiling.fit_regress
.. autofunction:: pv_uncertainty.uncertainty.study_soiling.generate_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_soiling.generate_sr_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_soiling.generate_sr_scenarios_v2
.. autofunction:: pv_uncertainty.uncertainty.study_soiling.get_cleaning_events
.. autofunction:: pv_uncertainty.uncertainty.study_soiling.sr_fig


uncertainty.study_temp_ambiant
==============================

.. automodule:: pv_uncertainty.uncertainty.study_temp_ambiant

.. autofunction:: pv_uncertainty.uncertainty.study_temp_ambiant.atemp_scenarios


uncertainty.study_temp_module
=============================

.. automodule:: pv_uncertainty.uncertainty.study_temp_module

.. autofunction:: pv_uncertainty.uncertainty.study_temp_module.get_data_site
.. autofunction:: pv_uncertainty.uncertainty.study_temp_module.get_file_site
.. autofunction:: pv_uncertainty.uncertainty.study_temp_module.import_iea_tempdata
.. autofunction:: pv_uncertainty.uncertainty.study_temp_module.temp_scenarios
.. autofunction:: pv_uncertainty.uncertainty.study_temp_module.temp_scenarios_module
.. autofunction:: pv_uncertainty.uncertainty.study_temp_module.temp_scenarios_v2


uncertainty.study_tmy
=====================

.. automodule:: pv_uncertainty.uncertainty.study_tmy



uncertainty.study_wind
======================

.. automodule:: pv_uncertainty.uncertainty.study_wind

.. autofunction:: pv_uncertainty.uncertainty.study_wind.wind_scenarios


uncertainty.uncertainty_config
==============================

.. automodule:: pv_uncertainty.uncertainty.uncertainty_config

.. autofunction:: pv_uncertainty.uncertainty.uncertainty_config.load_bsrn_data
.. autofunction:: pv_uncertainty.uncertainty.uncertainty_config.load_pvlive_data


utils.helio_fmt
===============

.. automodule:: pv_uncertainty.utils.helio_fmt

.. autofunction:: pv_uncertainty.utils.helio_fmt.q_plot
.. autofunction:: pv_uncertainty.utils.helio_fmt.random_plot
.. autofunction:: pv_uncertainty.utils.helio_fmt.setup_helio_plt


utils.vizualization_tools
=========================

.. automodule:: pv_uncertainty.utils.vizualization_tools

.. autofunction:: pv_uncertainty.utils.vizualization_tools.ac_graph
.. autofunction:: pv_uncertainty.utils.vizualization_tools.ac_monthly_boxplot
.. autofunction:: pv_uncertainty.utils.vizualization_tools.ac_yearlypr_graph
.. autofunction:: pv_uncertainty.utils.vizualization_tools.cldr_heatmap
.. autofunction:: pv_uncertainty.utils.vizualization_tools.cumulepi_scenario_calc
.. autofunction:: pv_uncertainty.utils.vizualization_tools.dc_ac_seasonal_plot
.. autofunction:: pv_uncertainty.utils.vizualization_tools.epi_proj_plot
.. autofunction:: pv_uncertainty.utils.vizualization_tools.epi_scenario_calc
.. autofunction:: pv_uncertainty.utils.vizualization_tools.epif_scenario_calc
.. autofunction:: pv_uncertainty.utils.vizualization_tools.loss_sankey_diagram
.. autofunction:: pv_uncertainty.utils.vizualization_tools.monthly_irrad
.. autofunction:: pv_uncertainty.utils.vizualization_tools.pi_scenario_calc
.. autofunction:: pv_uncertainty.utils.vizualization_tools.projection_plot
.. autofunction:: pv_uncertainty.utils.vizualization_tools.uncertainty_global_visualization
.. autofunction:: pv_uncertainty.utils.vizualization_tools.uncertainty_global_visualization_v2
.. autofunction:: pv_uncertainty.utils.vizualization_tools.uncertainty_global_visualization_v3
.. autofunction:: pv_uncertainty.utils.vizualization_tools.weather_seasonal_plot
.. autofunction:: pv_uncertainty.utils.vizualization_tools.yearly_ac_hist


