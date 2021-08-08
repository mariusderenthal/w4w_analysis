# load packages -----------------------------------------------------------
pacman::p_load(vroom, here,
               tidyverse,hrbrthemes,viridis, corrplot,GGally,brms,tidybayes,modelr,
               bayesplot,rstanarm, loo,projpred,caret,splines,broom.mixed,ROCR , sjstats,
               HSAUR3, flextable, wesanderson, ggthemes, splitstackshape, patchwork, PNWColors,ggExtra,tseries,gmp,geosphere,
               survival, shinystan)


# config ------------------------------------------------------------------

# load data ---------------------------------------------------------------
data <- vroom(here("data/03_processed/sample_points/sample_points_0624.csv")) # one could also check out feather 
#adjacency_matrix <- read.table("adjacency_matrix.txt",header=TRUE,row.names=1, check.names=FALSE)
#adjacency_matrix_mat <- data.matrix(adjacency_matrix)

# tidy data ---------------------------------------------------------------
# remove all class == 50 as we are not interested in forest class as predictor
data<-data[!(data$class==50),]
# remove all year == 2003 as we do not have dist_afforastation in that year
data<-data[!(data$year==2003),]
# remove all year == 2015 as no afforestation is taking place in 14/15 (NAs)
data<-data[!(data$year==2015),]
# remove all year == 2019 as it is the last year and we do not have data for 2020
data<-data[!(data$year==2019),]
# remove all neigh_tot <=5 as we want points with at least 6 neighbouring cells
#data<-data[!(data$neigh_tot<=4),]

sum(data$afforestation)/nrow(data)
# remove uncessary columns
data <- data[, !(colnames(data) %in% c("...1", "count", "count_forest"))]

# data types
# categorical values
data$MPIO_CNM_1 <- as.factor(data$MPIO_CNM_1)
levels(data$MPIO_CNM_1)[levels(data$MPIO_CNM_1) == "Barrancabermeja"] <- 1
levels(data$MPIO_CNM_1)[levels(data$MPIO_CNM_1) == "Puerto Wilches"] <- 2
levels(data$MPIO_CNM_1)[levels(data$MPIO_CNM_1) == "Sabana De Torres"] <- 3
data$class <- as.factor(data$class)
#data$afforestation <- as.factor(data$afforestation)
data$year <- as.factor(data$year)
data$plot_id <- as.factor(data$plot_id)



# standardization ---------------------------------------------------------
# data <- data %>% mutate_at(c("altitude","slope","curvature","aspect",
#                              "AWcTS","WWP","ORCDRC","PHIHOX",
#                              "dist_pop","dist_river","dist_po_mill","dist_afforestation"), ~(scale(.)))

data <-
  data %>% 
  mutate(altitude_z = (altitude - mean(altitude)) / sd(altitude),
         slope_z = (slope - mean(slope)) / sd(slope),
         curvature_z = (curvature - mean(curvature)) / sd(curvature),
         aspect_z = (aspect - mean(aspect)) / sd(aspect),
         
         AWcTS_z = (AWcTS - mean(AWcTS)) / sd(AWcTS),
         WWP_z = (WWP - mean(WWP)) / sd(WWP),
         ORCDRC_z = (ORCDRC - mean(ORCDRC)) / sd(ORCDRC),
         PHIHOX_z = (PHIHOX - mean(PHIHOX)) / sd(PHIHOX),
         
         dist_pop_z = (dist_pop - mean(dist_pop)) / sd(dist_pop),
         dist_river_z = (dist_river - mean(dist_river)) / sd(dist_river),
         dist_po_mill_z = (dist_po_mill - mean(dist_po_mill)) / sd(dist_po_mill),
         dist_afforestation_z = (dist_afforestation - mean(dist_afforestation)) / sd(dist_afforestation))


# feature engineering -----------------------------------------------------
# data$neigh_crop = data$`10`/data$neigh_tot
# data$neigh_mosaic_crop = data$`30`/data$neigh_tot
# data$neigh_mosaic_nat = data$`40`/data$neigh_tot
# data$neigh_forest = data$`50`/data$neigh_tot
# data$neigh_shrub = data$`120`/data$neigh_tot
# 
# data[c("neigh_crop",
#        "neigh_mosaic_crop", 
#        "neigh_mosaic_nat", 
#        "neigh_forest", 
#        "neigh_shrub")][is.na
#                        (data[c("neigh_crop",
#                                "neigh_mosaic_crop", 
#                                "neigh_mosaic_nat", 
#                                "neigh_forest", 
#                                "neigh_shrub")])] <- 0
# 
# data <- data[, !(colnames(data) %in% c("10","30","40", "50", "120"))]
# data <- data %>% mutate_at(c("neigh_crop",
#                              "neigh_mosaic_crop",
#                              "neigh_mosaic_nat",
#                              "neigh_forest",
#                              "neigh_shrub"), ~(scale(.)))
# 
# 
# 
# data$dam_construction <- 1
# data$dam_construction[data$year >2007 & data$year < 2014] <- 2
# data$dam_construction[data$year >2013 ] <- 3
# data$dam_construction <- as.factor(data$dam_construction)


# sampling ----------------------------------------------------------------
# filter based on x and y plot for autcorrelation
x_min = min(data$x)
x_max = max(data$x)
x_filter = seq(from = x_min, to = x_max, by = 2)
y_min = min(data$y)
y_max = max(data$y)
y_filter = seq(from = y_min, to = y_max, by = 2)

years <- unique(data$year)
data_samp = data.frame()
for (year in years){
  rand <- rbinom(1, 1, 0.5)
  data_year<-data[data$year == year,]
  data_year = subset(data_year, x %in% (x_filter+ rand))
  data_year = subset(data_year, y %in% (y_filter+ rand))
  data_samp = rbind(data_samp, data_year) 
}

#data_samp = subset(data, x %in% x_filter)
#data_samp = subset(data_samp, y %in% y_filter)

data_samp <- stratified(data_samp, c("class", "year", "afforestation", "MPIO_CNM_1"), 0.25)
rm(data, data_year, rand, x_filter, x_max, x_min, y_filter, y_max, y_min, year, years)


# data exploration --------------------------------------------------------
data_samp %>% 
  summarise(grand_mean = mean(afforestation))

data_samp %>% 
  group_by(class) %>% 
  summarise(mean = mean(afforestation))
# adjaceny_matrix ---------------------------------------------------------
# data_geo <- select(data_samp, x, y, x_coords, y_coords, plot_id)
# data_geo_unique <- distinct(data_geo, .keep_all = FALSE)
# #data_geo_unique_sub <- data_geo_unique[data_geo_unique$plot_id <=1000,]
# dist = distm(data_geo_unique[,3:4], data_geo_unique[,3:4], fun = distGeo)
# 
# 
# rownames(dist) = data_geo_unique$plot_id
# colnames(dist) = data_geo_unique$plot_id
# 
# dist[dist< 500 & dist > 0]<-1
# dist[dist >= 500] <- 0
# rm(data_geo,data_geo_unique)
# adjacency_matrix <- dist
# rm(dist)
# #adjacency_matrix$rowsum = rowSums(adjacency_matrix)
# 
# thresh <- 0
# test <- adjacency_matrix[rowSums(adjacency_matrix)> thresh,]
# adjacency_matrix <- test
# plots <- rownames(adjacency_matrix)
# test <- adjacency_matrix[,plots]
# adjacency_matrix <- test
# 
# data_samp <- data_samp[data_samp$plot_id %in% plots ,]



# likelihood --------------------------------------------------------------
# bernoulli 
# binomial and trial = 1

# link function -----------------------------------------------------------
#logit (default)
#cloglog (It is best used when the probability of an event is very small or very large)
  # https://stats.stackexchange.com/questions/379714/binomial-regression-logit-vs-cloglog
  # https://www.rensvandeschoot.com/tutorials/discrete-time-survival/
  # https://bookdown.org/content/4253/extending-the-discrete-time-hazard-model.html#using-the-complementary-log-log-link-to-specify-a-discrete-time-hazard-model
  # https://community.alteryx.com/t5/Alteryx-Designer-Knowledge-Base/Selecting-a-Logistic-Regression-Model-Type-Logit-Probit-or/ta-p/111269

# priors ------------------------------------------------------------------
# priors for intercept
  # normal(0, 1.5) : https://bookdown.org/content/4857/god-spiked-the-integers.html#logistic-regression-prosocial-chimpanzees.
  # normal(0, 1) : https://calogica.com/r/rstan/2020/07/05/season-pass-hierarchical-modelng-r-stan-brms.html#modeling-interactions
  # student_t(6, 0, 1.5) : https://discourse.mc-stan.org/t/default-priors-for-logistic-regression-coefficients-in-brms/13742 - less a priori confidence 
  # student_t(7, 0, 2.5) : https://avehtari.github.io/modelselection/diabetes.html - less a priori confidence 

# priors for b
  # normal(0, 0.5) : https://bookdown.org/content/4857/god-spiked-the-integers.html#logistic-regression-prosocial-chimpanzees.
  # normal(0, 1) : https://calogica.com/r/rstan/2020/07/05/season-pass-hierarchical-modelng-r-stan-brms.html#modeling-interactions
  # student_t(6, 0, 1.5) : https://discourse.mc-stan.org/t/default-priors-for-logistic-regression-coefficients-in-brms/13742 - less a priori confidence 
  # student_t(7, 0, 2.5) : https://avehtari.github.io/modelselection/diabetes.html - less a priori confidence 


# priors for sd
  # normal(0, 1) : https://calogica.com/r/rstan/2020/07/05/season-pass-hierarchical-modelng-r-stan-brms.html#modeling-interactions
  # exponential(1) : https://bookdown.org/content/4857/models-with-memory.html#example-multilevel-tadpoles
  # normal(0, 1) : https://bookdown.org/content/4857/models-with-memory.html#example-multilevel-tadpoles
  
# priors for cor
  # lkj(2) : https://bookdown.org/content/4857/adventures-in-covariance.html#advanced-varying-slopes


# priors sets
prior_McE = c(prior(normal(0, 1.5), class = Intercept),
              prior(normal(0, 0.5), class = b),
              prior(normal(0, 1), class = sd),
              prior(lkj(2), class = cor))

prior_lessI = c(prior(student_t(6, 0, 1.5), class = Intercept),
                prior(student_t(6, 0, 1.5), class = b),
                prior(normal(0, 1), class = sd),
                prior(lkj(2), class = cor))





# base models --------------------------------------------------------------
stand_model_log <- brm(data = data_samp, 
                      
                      family = bernoulli(link = "logit"),
                      
                      afforestation ~ 
                        dist_afforestation_z +  dist_pop_z + dist_po_mill_z + dist_river_z +
                        slope_z + aspect_z +
                        ORCDRC_z + AWcTS_z +  
                        class + MPIO_CNM_1 + year,

                      iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                      seed = 13,
                      sample_prior = T,
                      control = list(adapt_delta = 0.90),
                      file = here("models/02_model_output/stand_model_log"))

stand_model_log_posterior <- as.array(stand_model_log)
stand_model_log <- add_criterion(stand_model_log, c("loo", "waic"))



base_model_log <- brm(data = data_samp, 
                  
                  family = bernoulli(link = "logit"),
                  
                  afforestation ~ 
                    dist_afforestation_z +  dist_pop_z + dist_po_mill_z + dist_river_z +
                    slope_z + aspect_z +
                    ORCDRC_z + AWcTS_z +  
                    class + MPIO_CNM_1 + year,
                  
                  prior = c(prior(normal(0, 1.5), class = b),
                            prior(normal(0, 1.5), class = Intercept)),

                  iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                  seed = 13,
                  sample_prior = T,
                  control = list(adapt_delta = 0.90),
                  file = here("models/02_model_output/base_model_log"))

base_model_log_posterior <- as.array(base_model_log)
base_model_log <- add_criterion(base_model_log, c("loo", "waic"))



base_model_log_0 <- brm(data = data_samp, 
                      
                      family = bernoulli(link = "logit"),
                      
                      afforestation ~
                        dist_afforestation_z +  dist_river_z +# dist_pop_z + dist_po_mill_z +
                        slope_z + aspect_z +
                        ORCDRC_z, #AWcTS_z + 
                      
                      prior = c(prior(normal(0, 1.5), class = b),
                                prior(normal(0, 1.5), class = Intercept)),

                      
                      iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                      seed = 13,
                      sample_prior = T,
                      control = list(adapt_delta = 0.90),
                      file = here("models/02_model_output/base_model_log_0"))

base_model_log_0_posterior <- as.array(base_model_log_0)
base_model_log_0 <- add_criterion(base_model_log_0, c("loo", "waic"))


# interaction model -------------------------------------------------
final_model_inter_0 <- brm(data = data_samp,
                      family = bernoulli(link = "logit"),
                      afforestation ~ 0 +
                        
                        # covariates I just want to account for, not interested in 
                        slope_z + aspect_z + ORCDRC_z +
                        
                        # covariates I'm interested in 
                        dist_afforestation_z + class + dist_river_z + 
                        
                        # interactions terms
                        dist_afforestation_z:year + class:year + dist_river_z:year +
                        dist_afforestation_z:MPIO_CNM_1 + class:MPIO_CNM_1 + dist_river_z:MPIO_CNM_1,
              
                        # multilevel terms
                        #(1 + dist_afforestation_z + class + dist_river_z + 
                        #   dist_afforestation_z*year + class*year + dist_river_z*year| MPIO_CNM_1),
                  
                      prior = c(#prior(normal(0, 1.5), class = Intercept),
                                prior(normal(0, 1.5), class = b)),
                                #prior(normal(0, 1), class = sd)),
                                #prior(lkj(2), class = cor)),
                      
                      iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                      seed = 13,
                      sample_prior = T,
                      control = list(adapt_delta = 0.95),
                      file = here("models/02_model_output/final_model_inter_0"))

final_model_inter_0_posterior <- as.array(final_model_inter_0)
final_model_inter_0 <- add_criterion(final_model_inter_0, c("loo", "waic"))



final_model_inter_1 <- brm(data = data_samp,
                           family = bernoulli(link = "logit"),
                           afforestation ~ 1 +
                             
                             # covariates I just want to account for, not interested in 
                             slope_z + aspect_z + ORCDRC_z +
                             
                             # covariates I'm interested in 
                             dist_afforestation_z + class + dist_river_z + 
                             
                             # interactions terms
                             dist_afforestation_z:year + class:year + dist_river_z:year +
                             dist_afforestation_z:MPIO_CNM_1 + class:MPIO_CNM_1 + dist_river_z:MPIO_CNM_1,
                           
                           # multilevel terms
                           #(1 + dist_afforestation_z + class + dist_river_z + 
                           #   dist_afforestation_z*year + class*year + dist_river_z*year| MPIO_CNM_1),
                           
                           prior = c(prior(normal(0, 1.5), class = Intercept),
                             prior(normal(0, 1.5), class = b)),
                           #prior(normal(0, 1), class = sd)),
                           #prior(lkj(2), class = cor)),
                           
                           iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                           seed = 13,
                           sample_prior = T,
                           control = list(adapt_delta = 0.95),
                           file = here("models/02_model_output/final_model_inter_1"))

final_model_inter_1_posterior <- as.array(final_model_inter_1)
final_model_inter_1 <- add_criterion(final_model_inter_1, c("loo", "waic"))



# random slope model ------------------------------------------------
final_model_RS_0 <- brm(data = data_samp,
                      family = bernoulli(link = "logit"),
                      afforestation ~ 0 +
                        
                        # covariates I just want to account for, not interested in 
                        slope_z + aspect_z + ORCDRC_z +
                        
                        # covariates I'm interested in 
                        dist_afforestation_z + class + dist_river_z + 
                        
                        # multilevel terms
                        (0 + dist_afforestation_z + dist_river_z + class | MPIO_CNM_1) +
                        (0 + dist_afforestation_z + dist_river_z + class  | year),
                       
                       prior = c(#prior(normal(0, 1.5), class = Intercept),
                                 prior(normal(0, 1.5), class = b),
                                 prior(normal(0, 1), class = sd),
                                 prior(lkj(2), class = cor)),
                       
                       iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                       seed = 13,
                       sample_prior = T,
                       control = list(adapt_delta = 0.95),
                       file = here("models/02_model_output/final_model_RS_0"))

final_model_RS_0_posterior <- as.array(final_model_RS_0)
final_model_RS_0 <- add_criterion(final_model_RS_0, c("loo", "waic"))


final_model_RS_1 <- brm(data = data_samp,
                        family = bernoulli(link = "logit"),
                        afforestation ~ 1 +
                          
                          # covariates I just want to account for, not interested in 
                          slope_z + aspect_z + ORCDRC_z +
                          
                          # covariates I'm interested in 
                          dist_afforestation_z + class + dist_river_z + 
                          
                          # multilevel terms
                          (0 + dist_afforestation_z + dist_river_z + class | MPIO_CNM_1) +
                          (0 + dist_afforestation_z + dist_river_z + class  | year),
                        
                        prior = c(prior(normal(0, 1.5), class = Intercept),
                                  prior(normal(0, 1.5), class = b),
                                  prior(normal(0, 1), class = sd),
                                  prior(lkj(2), class = cor)),
                        
                        iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                        seed = 13,
                        sample_prior = T,
                        control = list(adapt_delta = 0.95),
                        file = here("models/02_model_output/final_model_RS_1"))

final_model_RS_1_posterior <- as.array(final_model_RS_1)
final_model_RS_1 <- add_criterion(final_model_RS_1, c("loo", "waic"))




# random intercept and slope model ----------------------------------
final_model_RIS_0 <- brm(data = data_samp,
                   family = bernoulli(link = "logit"),
                   afforestation ~ 0 +
                     
                     # covariates I just want to account for, not interested in 
                     slope_z + aspect_z + ORCDRC_z +
                     
                     # covariates I'm interested in 
                     dist_afforestation_z + class + dist_river_z + 
                     
                     # multilevel terms
                     (1 + dist_afforestation_z + dist_river_z + class | MPIO_CNM_1) +
                     (1 + dist_afforestation_z + dist_river_z + class  | year),
                   
                   prior = c(#prior(normal(0, 1.5), class = Intercept),
                             prior(normal(0, 1.5), class = b),
                             prior(normal(0, 1), class = sd),
                             prior(lkj(2), class = cor)),
                   
                   iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                   seed = 13,
                   sample_prior = T,
                   control = list(adapt_delta = 0.95),
                   file = here("models/02_model_output/final_model_RIS_0"))
                     
final_model_RIS_0_posterior <- as.array(final_model_RIS_0)
final_model_RIS_0 <- add_criterion(final_model_RIS_0, c("loo", "waic"))    


final_model_RIS_1 <- brm(data = data_samp,
                         family = bernoulli(link = "logit"),
                         afforestation ~ 1 +
                           
                           # covariates I just want to account for, not interested in 
                           slope_z + aspect_z + ORCDRC_z +
                           
                           # covariates I'm interested in 
                           dist_afforestation_z + class + dist_river_z + 
                           
                           # multilevel terms
                           (1 + dist_afforestation_z + dist_river_z + class | MPIO_CNM_1) +
                           (1 + dist_afforestation_z + dist_river_z + class  | year),
                         
                         prior = c(prior(normal(0, 1.5), class = Intercept),
                           prior(normal(0, 1.5), class = b),
                           prior(normal(0, 1), class = sd),
                           prior(lkj(2), class = cor)),
                         
                         iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                         seed = 13,
                         sample_prior = T,
                         control = list(adapt_delta = 0.95),
                         file = here("models/02_model_output/final_model_RIS_1"))

final_model_RIS_1_posterior <- as.array(final_model_RIS_1)
final_model_RIS_1 <- add_criterion(final_model_RIS_1, c("loo", "waic"))   



# non-linear model approach --------------------------------------------------------
final_model_nl2 <- 
  brm(data = data_samp,
      family = bernoulli(link = "logit"),
      bf(afforestation ~ 0 + a + h + slope_z + aspect_z + ORCDRC_z , 
         a ~ 0 + class, 
         h ~ 0 + MPIO_CNM_1,
         nl = TRUE),
      prior = c(prior(normal(0, 1.5), nlpar = a),
                prior(normal(0, 1.5), nlpar = h),
                prior(normal(0, 1.5), class = b)),
      iter = 2000, warmup = 1000, chains = 4, cores = 4,
      seed = 5,
      file = here("models/02_model_output/final_model_nl2"))


final_model_nl_interaction3 <- 
  brm(data = data_samp,
      family = bernoulli(link = "logit"),
      bf(afforestation ~ 0 +  
           
           class +
           distaffo +  distriver +
           slope + aspect +
           ORCDRC +
           
           yearaffo*dist_afforestation_z + 
           yearclass*class + 
           yearriver*dist_river_z +
           
           MPIOaffo*dist_afforestation_z + 
           MPIOclass*class + 
           MPIOriver*dist_river_z , 
         
         
         class ~ 0 + class,
         distaffo ~ 0 + dist_afforestation_z,
         distriver ~ 0 + dist_river_z,
         slope ~ 0 + slope_z, 
         aspect ~ 0 + aspect_z,
         ORCDRC ~ 0 + ORCDRC_z,
           
         yearaffo ~ 0 + year,
         yearclass ~ 0 + year,
         yearriver~ 0 + year,
         
         MPIOaffo ~ 0 + MPIO_CNM_1,
         MPIOclass ~ 0 + MPIO_CNM_1,
         MPIOriver~ 0 + MPIO_CNM_1,
         
         nl = TRUE),
      prior = c(prior(normal(1, 0.1), class = b, nlpar = class),
                prior(normal(1, 0.1), class = b, nlpar = distaffo),
                prior(normal(1, 0.1), class = b, nlpar = distriver),
                prior(normal(1, 0.1), class = b, nlpar = slope),
                prior(normal(1, 0.1), class = b, nlpar = aspect),
                prior(normal(1, 0.1), class = b, nlpar = ORCDRC),
                
                prior(normal(1, 0.1), class = b, nlpar = yearaffo),
                prior(normal(1, 0.1), class = b, nlpar = yearclass),
                prior(normal(1, 0.1), class = b, nlpar = yearriver),
                
                prior(normal(1, 0.1), class = b, nlpar = MPIOaffo),
                prior(normal(1, 0.1), class = b, nlpar = MPIOclass),
                prior(normal(1, 0.1), class = b, nlpar = MPIOriver)),
      iter = 2000, warmup = 1000, chains = 4, cores = 4,
      seed = 5,
      file = here("models/02_model_output/final_model_nl_interaction3"))

#final_model_RIS_0_posterior <- as.array(final_model_RIS_0)
final_model_nl_interaction <- add_criterion(final_model_nl_interaction, c("loo", "waic")) 
final_model_nl_interaction2 <- add_criterion(final_model_nl_interaction2, c("loo", "waic")) 
final_model_nl_interaction3 <- add_criterion(final_model_nl_interaction3, c("loo", "waic")) 

# anova model approach -------------------------------------------------------------
final_model_anova <- 
  brm(data = data_samp,
      family = bernoulli(link = "logit"),
      afforestation ~ 1 + (1 | class) + (1 | MPIO_CNM_1),
      prior = c(prior(normal(0, 0.5), class = Intercept),
                prior(exponential(1), class = sd)),
      iter = 2000, warmup = 1000, chains = 4, cores = 4,
      seed = 5,
      file = here("models/02_model_output/final_model_anova"))

# final final final -------------------------------------------------------
final_model_inter <- brm(data = data_samp,
                         family = bernoulli(link = "logit"),
                         afforestation ~ 1 +
                           
                           # covariates I just want to account for, not interested in 
                           slope_z + aspect_z + ORCDRC_z +
                           
                           # covariates I'm interested in 
                           dist_afforestation_z  + dist_river_z + 
                           MPIO_CNM_1 + year + class +
                           
                           # interactions terms
                           class:year + dist_afforestation_z:year + dist_river_z:year +
                           class: MPIO_CNM_1 + dist_afforestation_z:MPIO_CNM_1+ dist_river_z:MPIO_CNM_1,
                         
                         prior = c(prior(normal(0, 1.5), class = Intercept),
                                   prior(normal(0, 1.5), class = b)),
                         
                         iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                         seed = 13,
                         sample_prior = T,
                         control = list(adapt_delta = 0.95),
                         file = here("models/02_model_output/final_model_inter"))

final_model_inter <- add_criterion(final_model_inter, c("loo", "waic"))


final_model_RIS <- brm(data = data_samp,
                       family = bernoulli(link = "logit"),
                       afforestation ~ 1 +
                         
                         # covariates I just want to account for, not interested in 
                         slope_z + aspect_z + ORCDRC_z +
                         
                         # covariates I'm interested in 
                         dist_afforestation_z + class + dist_river_z + 
                         
                         # multilevel terms
                         (1 + dist_afforestation_z + class + dist_river_z | MPIO_CNM_1) +
                         (1 + dist_afforestation_z + class + dist_river_z | year),
                       
                       prior = c(prior(normal(0, 1.5), class = Intercept),
                                 prior(normal(0, 1.5), class = b),
                                 prior(normal(0, 1), class = sd),
                                 prior(lkj(2), class = cor)),
                       
                       iter = 2000, warmup = 1000, chains = 4, cores = 4,  
                       seed = 13,
                       sample_prior = T,
                       control = list(adapt_delta = 0.95),
                       file = here("models/02_model_output/final_model_RIS"))

final_model_RIS <- add_criterion(final_model_RIS, c("loo", "waic"))

loo_compare(final_model_inter, final_model_RIS, criterion = "loo") %>% print(simplify = F)

# convergence -------------------------------------------------------------
mcmc_trace(final_model_inter, regex_pars = c("b_year"), facet_args = list(nrow = 2))
mcmc_trace(final_model_RIS, regex_pars = c("b_"), facet_args = list(nrow = 2))


mcmc_plot(final_model_inter, type = "trace")
mcmc_plot(final_model_inter, type = "acf_bar")

mcmc_plot(final_model_RIS, type = "trace")
mcmc_plot(final_model_RIS, type = "acf_bar")


# model comparison --------------------------------------------------------
loo_compare(final_model_inter, final_model_RIS,criterion = "loo") %>% print(simplify = F)
model_weights(final_model_inter, final_model_RIS, criterion = "loo") %>% round(digits = 2)

# prior predictive checkts ------------------------------------------------
# McElreath
bind_rows(prior_samples(stand_model_log),
          prior_samples(base_model_log)) %>% 
  mutate(p = inv_logit_scaled(Intercept),
         w = factor(rep(c("stand_model_log","base_model_log"), each = n() / 2),
                    levels = c("stand_model_log","base_model_log"))) %>% 
  
  # plot
  ggplot(aes(x = p, fill = w)) +
  geom_density(size = 0, alpha = 3/4, adjust = 0.1) +
  scale_fill_manual(expression(italic(w)), values = wes_palette("Moonrise2")) +
  scale_y_continuous(NULL, breaks = NULL) +
  labs(title = expression(alpha%~%Normal(0*", "*italic(w))),
       x = "prior prob afforestation")


# prior <-
#   bind_rows(prior_samples(stand_model_log),
#             prior_samples(base_model_log)) %>% 
#   mutate(w  = factor(rep(c(10, 0.5), each = n() / 2),
#                      levels = c(10, 0.5)),
#          p1 = inv_logit_scaled(Intercept + b),
#          p2 = inv_logit_scaled(Intercept + b)) %>% 
#   mutate(diff = abs(p1 - p2)) 
# 
# # plot
# prior %>% 
#   ggplot(aes(x = diff, fill = w)) +
#   geom_density(size = 0, alpha = 3/4, adjust = 0.1) +
#   scale_fill_manual(expression(italic(w)), values = wes_palette("Moonrise2")[c(4, 2)]) +
#   scale_y_continuous(NULL, breaks = NULL) +
#   labs(title = expression(alpha%~%Normal(0*", "*italic(w))),
#        x = "prior diff between treatments")


# prior %>% 
#   group_by(w) %>% 
#   summarise(mean = mean(diff))


mcmc_areas(
  as.array(stand_model_log), 
  #pars = c("b_ulr_Intercept", "b_omega_Intercept",
  #         "b_phi_Intercept",
  #         "sd_AY__ulr_Intercept", "sigma"),
  prob = 0.8, # 80% intervals
  prob_outer = 0.99, # 99%
  point_est = "mean"
) + ggplot2::labs(
  title = "Prior parameter distributions",
  subtitle = "with medians and 80% intervals"
)


# interpretation ----------------------------------------------------------
summary(final_model_inter, prob = 0.95)
mcmc_areas(
  final_model_RIS,
  regex_pars = "sd_",
  prob = 0.95, 
  point_est = "median",
  area_method = "equal height"
) +
  geom_vline(xintercept = 0, color = "red", alpha = 0.6, lwd = .8, linetype = "dashed") +
  labs(
    title = "Effect of Bundle Promotion on Sales"
  )
exp(fixef(base_model_log))

# class is is not worth putting into any interaction or higher level term

# evaluation --------------------------------------------------------------




# questions ---------------------------------------------------------------
# Interaction Effects vs Random Effects
  # https://stats.stackexchange.com/questions/366006/regression-interaction-effects-vs-random-effects
  # https://www.reddit.com/r/statistics/comments/73cakv/what_is_the_difference_between_random_slopes_by/
  # https://stats.stackexchange.com/questions/151668/difference-between-a-random-slope-intercept-model-and-an-ancova-with-an-interact
  # https://stats.stackexchange.com/questions/4700/what-is-the-difference-between-fixed-effect-random-effect-and-mixed-effect-mode

# Group size for multilevel modelling
  # https://stats.stackexchange.com/questions/37647/what-is-the-minimum-recommended-number-of-groups-for-a-random-effects-factor
  # --> Don"t mind the limit

# Odds Ratio 
  # https://stats.idre.ucla.edu/other/mult-pkg/faq/general/faq-how-do-i-interpret-odds-ratios-in-logistic-regression/

# Grand Mean Centering, Centering Within Cluster or Standarization
  # https://philippmasur.de/2018/05/23/how-to-center-in-multilevel-models/
  # https://www.youtube.com/watch?v=b1NGpsBRokE
  # https://www.researchgate.net/publication/247503516_The_Effect_of_Different_Forms_of_Centering_in_Hierarchical_Linear_Models
  # https://quantscience.rbind.io/2020/02/04/bayesian-mlm-with-group-mean-centering/#group-mean-centering-treating-group-means-as-latent-variables
  # --> Not doing it

# brms formula and priors
  # https://rdrr.io/cran/brms/man/brmsformula.html
  # https://rdrr.io/cran/brms/man/get_prior.html
  # https://rdrr.io/cran/brms/man/set_prior.html
  # --> 0 + means forcing the overall intercept out. Each term gets its own absolute 

# brms Multilevel examples
  # https://www.rensvandeschoot.com/tutorials/brms-started/
  # https://www.rensvandeschoot.com/tutorials/generalised-linear-models-with-brms/
  # https://www.rensvandeschoot.com/tutorials/brms-priors/
  # https://calogica.com/r/rstan/2020/07/05/season-pass-hierarchical-modelng-r-stan-brms.html#modeling-interactions
  # https://biol609.github.io/lectures/23c_brms_prediction.html#241_assessing_convergence

# link function (time discrete survival analysis)
  # https://www.rensvandeschoot.com/tutorials/discrete-time-survival/
  # https://bookdown.org/content/4253/extending-the-discrete-time-hazard-model.html#using-the-complementary-log-log-link-to-specify-a-discrete-time-hazard-model

# categorical variables - non-linear syntax
  # https://bookdown.org/content/4857/the-many-variables-the-spurious-waffles.html#many-categories.
  # https://discourse.mc-stan.org/t/indexing-approach-to-predictors/7898/4
  # https://solomonkurz.netlify.app/post/2020-12-09-multilevel-models-and-the-index-variable-approach/
  # ---> use categorical 

# which plots??
# predictors as fixed and random?
# divergent transitions ??
# model comparison??

get_prior(data = data_samp,
          family = bernoulli(link = "logit"),
          bf(afforestation ~ 1 +
               
               # covariates I just want to account for, not interested in 
               slope_z + aspect_z + ORCDRC_z +
               
               # covariates I'm interested in 
               dist_afforestation_z  + dist_river_z + 
               MPIO_CNM_1 + year + class +
               
               # interactions terms
               class:year + dist_afforestation_z:year + dist_river_z:year +
               class: MPIO_CNM_1 + dist_afforestation_z:MPIO_CNM_1+ dist_river_z:MPIO_CNM_1))


get_prior(data = data_samp,family = bernoulli(link = "logit"),formula =
            afforestation ~ 1 + (1 | class) + (1 | MPIO_CNM_1))
               








