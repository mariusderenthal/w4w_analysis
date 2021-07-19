# load_packages -----------------------------------------------------------
pacman::p_load(ggdag)
theme_set(theme_dag())



afforestation_dam <- dagify(affo ~ 
                              # Topography and soil conditions
                              slope + aspect +  ORCDRC  +
                              # Distance covariates
                              dist_pop + dist_river + dist_mill + dist_afforestation +
                              # Factors 
                              class + muni + dam_construction,
                            
                            # landcover class is influenced topography and soil conditions
                            class  ~ slope + aspect  + ORCDRC ,
                            
                            labels = c("affo" = "Afforestation", 
                                       "slope" = "Slope",
                                       "aspect" = "Aspect",
                                       "ORCDRC" = "Soil organic content",
                                       
                                       "dist_pop" = "Distance to city",
                                       "dist_river" = "Distance to river",
                                       "dist_mill" = "Distance to mill",
                                       "dist_afforestation" = "Distance nearest Afforestation",
                                       
                                       "class" = "Land cover class",
                                       "muni" = "Municipality",
                                       "dam_construction" = "Dam construction period"),
                            
                            #latent = "policy",
                            exposure = "dist_river",
                            outcome = "affo")

ggdag(afforestation_dam, text = FALSE, use_labels = "label")

ggdag_paths(afforestation_dam, text = FALSE, use_labels = "label", shadow = TRUE)
ggdag_adjustment_set(afforestation_dam, text = FALSE, use_labels = "label", shadow = TRUE)
ggdag_dseparated(afforestation_dam, controlling_for = c("class"), 
                 text = FALSE, use_labels = "label", collider_lines = FALSE)


# Causal effect modifiers: dist_river, 
# Outcome: Afforestation
# Treatment: Dam construction period
# Confounders:



# example -----------------------------------------------------------------
# smoking_ca_dag <- dagify(cardiacarrest ~ cholesterol,
#                          cholesterol ~ smoking + weight,
#                          smoking ~ unhealthy,
#                          weight ~ unhealthy,
#                          labels = c("cardiacarrest" = "Cardiac\n Arrest", 
#                                     "smoking" = "Smoking",
#                                     "cholesterol" = "Cholesterol",
#                                     "unhealthy" = "Unhealthy\n Lifestyle",
#                                     "weight" = "Weight"),
#                          latent = "unhealthy",
#                          exposure = "smoking",
#                          outcome = "cardiacarrest")
# 
# ggdag(smoking_ca_dag, text = FALSE, use_labels = "label")
# ggdag_paths(smoking_ca_dag, text = FALSE, use_labels = "label", shadow = TRUE)
# ggdag_adjustment_set(smoking_ca_dag, text = FALSE, use_labels = "label", shadow = TRUE)
# ggdag_dseparated(smoking_ca_dag, controlling_for = c("weight", "cholesterol"), 
#                  text = FALSE, use_labels = "label", collider_lines = FALSE)