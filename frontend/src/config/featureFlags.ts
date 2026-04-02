export const featureFlags = {
  landing_v1: true, // Set to true for development
  property_detail_v1: true, // Set to true for development
  analytics_enabled: true,
  seo_enabled: true,
};

export const isFeatureEnabled = (feature: keyof typeof featureFlags) => {
  // In production, this would check against a remote config or launchdarkly
  return featureFlags[feature] === true;
};
