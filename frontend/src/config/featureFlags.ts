export const featureFlags = {
  landing_v1: true, // Set to true for development
  property_detail_v1: true, // Set to true for development
  analytics_enabled: true,
  seo_enabled: true,
  fix_profile_dashboard_gridmap_v1: true,
  epic5_sprint10_payments_v1: true,
  epic6_sprint11_moveout_v1: true,
  epic7_sprint12_maintenance_v1: true,
  epic7_sprint13_onboarding_v1: true,
};

export const isFeatureEnabled = (feature: keyof typeof featureFlags) => {
  // In production, this would check against a remote config or launchdarkly
  return featureFlags[feature] === true;
};
