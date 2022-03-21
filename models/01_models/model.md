Bayesian modeling of oil palm expansion in Santander, Colombia - model
================
Marius Derenthal

# introduction

This document describes the workflow for the “Bayesian modeling of oil
palm expansion in Santander, Colombia” analysis.

Inspired, and partly duplicated, from A. Solomon Kurz, Paul Bürkner, and
Richard McElreath.

# workflow

1.  load data
2.  data processing
3.  modeling
4.  model comparison

# setup

## packages

``` r
# load packages -----------------------------------------------------------
pacman::p_load(vroom, here, tidyverse, hrbrthemes, viridis, corrplot, GGally,
               brms, tidybayes, modelr, bayesplot, rstanarm, loo, projpred, 
               caret, splines, broom.mixed, ROCR, sjstats, HSAUR3, flextable, 
               wesanderson, ggthemes, splitstackshape, patchwork, PNWColors, 
               ggExtra, tseries, gmp, geosphere, survival, shinystan, corrplot)
```

# analysis

## 1. load data

``` r
data <- vroom(here("data/03_processed/sample_points/sample_points_0311.csv")) 
```

## 2. data processing

### 2.1 round numbers

``` r
data = data %>% 
  mutate_at(vars(slope, aspect, dist_river, dist_po_mill, 
                 dist_road, dist_road_osm, dist_road_vias,
                 dist_afforestation ), funs(round(., 0)))
```

### 2.2 remove irrelevant data

``` r
# remove all class == 50 as we are not interested in forest class as predictor
data<-data[!(data$class==50),]
# remove all year == 2003 as we do not have dist_afforastation in that year
data<-data[!(data$year==2003),]
# remove all year == 2015 as no afforestation is taking place in 14/15 (NAs)
data<-data[!(data$year==2015),]
# remove all year == 2019 as it is the last year and we do not have data for 2020
data<-data[!(data$year==2019),]

# remove uncessary columns
data <- data[, !(colnames(data) %in% c("...1", "count", "count_forest"))]

# remove rows with incompltete soil features
data<-data[!(data$AWcTS==255),]
data<-data[!(data$WWP==255),]
data<-data[!(data$PHIHOX==0),]
data<-data[!(data$ORCDRC==0),]
```

### 2.3 change data types

``` r
# categorical values
data$MPIO_CNM_1 <- as.factor(data$MPIO_CNM_1)
levels(data$MPIO_CNM_1)[levels(data$MPIO_CNM_1) == "Barrancabermeja"] <- 1
levels(data$MPIO_CNM_1)[levels(data$MPIO_CNM_1) == "Puerto Wilches"] <- 2
levels(data$MPIO_CNM_1)[levels(data$MPIO_CNM_1) == "Sabana De Torres"] <- 3
data$class <- as.factor(data$class)
#data$afforestation <- as.factor(data$afforestation)
data$year <- as.factor(data$year)
data$plot_id <- as.factor(data$plot_id)

data$Oferta_Amb <- as.factor(data$Oferta_Amb)
levels(data$Oferta_Amb)[levels(data$Oferta_Amb) == "Áreas Para Producción"] <- 1
levels(data$Oferta_Amb)[levels(data$Oferta_Amb) == "Áreas Prioritarias para la Conservación"] <- 2
levels(data$Oferta_Amb)[levels(data$Oferta_Amb) == "Zonas urbanas"] <- 3
levels(data$Oferta_Amb)[levels(data$Oferta_Amb) == "Áreas de Protección Legal"] <- 4
```

### 2.4 standardization

``` r
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
         dist_road_z = (dist_road - mean(dist_road)) / sd(dist_road),
         dist_river_z = (dist_river - mean(dist_river)) / sd(dist_river),
         dist_po_mill_z = (dist_po_mill - mean(dist_po_mill)) / sd(dist_po_mill),
         dist_afforestation_z = (dist_afforestation - mean(dist_afforestation)) / sd(dist_afforestation))
```

### 2.5 sampling

``` r
# filter based on x and y plot id for autocorrelation
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

rm(data, data_year, rand, x_filter, x_max, x_min, y_filter, y_max, y_min, year, years)
saveRDS(data_samp,here('data/03_processed/sample_models/data_model'))

data_samp_samp <- stratified(data_samp, c("class", "year", "afforestation", "MPIO_CNM_1", "Oferta_Amb"), 0.25)
saveRDS(data_samp_samp,here('data/03_processed/sample_models/data_model_samp'))
```

## 3. modeling

``` r
data_samp_samp = readRDS(here('data/03_processed/sample_models/data_model_samp'))
```

### 3.1 base model

``` r
base_model <- brm(data = data_samp_samp, 
                  family = bernoulli(link = "logit"),
                  
                  afforestation ~ slope_z + aspect_z + 
                    ORCDRC_z  + PHIHOX_z + WWP_z + 
                    dist_pop_z +dist_po_mill_z + dist_road_z + dist_afforestation_z + 
                    (1|class) + (1|MPIO_CNM_1)+ (1|year)+ (1|Oferta_Amb),
                  
                  prior = c(prior(normal(0, 1), class = b),
                            prior(normal(0, 0.5), class = Intercept),
                            prior(exponential(1), class = sd)),
                  
                  iter = 2000, 
                  warmup = 1000, 
                  chains = 4, 
                  cores = 4,
                  seed = 13,
                  sample_prior = T,
                  control = list(adapt_delta = 0.95),
                  file = here("models/02_model_output/base_model"))

base_model <- add_criterion(base_model, c("loo", "waic"))
```

``` r
base_model_no_group <- brm(data = data_samp_samp,
                           family = bernoulli(link = "logit"),
                           
                           afforestation ~ 
                             slope_z + aspect_z +
                             ORCDRC_z  + PHIHOX_z + WWP_z +
                             dist_pop_z +dist_po_mill_z + dist_road_z + dist_afforestation_z,
                           
                           prior = c(prior(normal(0, 1), class = b),
                                     prior(normal(0, 0.5), class = Intercept)),
                           
                           iter = 2000, 
                           warmup = 1000, 
                           chains = 4, 
                           cores = 4,
                           seed = 13,
                           sample_prior = T,
                           control = list(adapt_delta = 0.95),
                           file = here("models/02_model_output/base_model_no_group"))

base_model_no_group <- add_criterion(base_model_no_group, c("loo", "waic"))
```

``` r
base_slim_model <- brm(data = data_samp_samp,
                       family = bernoulli(link = "logit"),
                       
                       afforestation ~
                         ORCDRC_z  + PHIHOX_z + WWP_z +
                         dist_pop_z + dist_afforestation_z +
                         (1|class) + (1|MPIO_CNM_1)+ (1|year)+ (1|Oferta_Amb),
                       
                       prior = c(prior(normal(0, 1), class = b),
                                 prior(normal(0, 0.5), class = Intercept),
                                 prior(exponential(1), class = sd)),
                       
                       iter = 2000, 
                       warmup = 1000, 
                       chains = 4, 
                       cores = 4,
                       seed = 13,
                       sample_prior = T,
                       control = list(adapt_delta = 0.95),
                       file = here("models/02_model_output/base_slim_model"))

base_slim_model <- add_criterion(base_slim_model, c("loo", "waic"))
```

### 3.2 multilevel (cross-classified) model

``` r
ris_slim_model <- brm(data = data_samp_samp,
                      family = bernoulli(link = "logit"),
                      
                      afforestation ~
                        ORCDRC_z + PHIHOX_z + WWP_z +
                        dist_pop_z + dist_afforestation_z +
                        # multilevel terms
                        (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | MPIO_CNM_1) +
                        (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | class) +
                        (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | year) +
                        (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | Oferta_Amb),
                      
                      prior = c(prior(normal(0, 0.5), class = Intercept),
                                prior(normal(0, 1), class = b),
                                prior(exponential(1), class = sd),
                                prior(lkj(2), class = cor)),
                      
                      iter = 2000, 
                      warmup = 1000, 
                      chains = 4, 
                      cores = 4,
                      seed = 13,
                      sample_prior = T,
                      control = list(adapt_delta = 0.95),
                      file = here("models/02_model_output/ris_slim_model"))

ris_slim_model <- add_criterion(ris_slim_model, c("loo", "waic"))
```

``` r
ris_medium_model <- brm(data = data_samp_samp,
                        family = bernoulli(link = "logit"),
                        
                        afforestation ~
                          slope_z + aspect_z + 
                          ORCDRC_z + PHIHOX_z + WWP_z +
                          dist_pop_z +dist_po_mill_z + dist_road_z + dist_afforestation_z +
                          # multilevel terms
                          (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | MPIO_CNM_1) +
                          (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | class) +
                          (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | year) +
                          (1 +   ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | Oferta_Amb),
                        
                        prior = c(prior(normal(0, 0.5), class = Intercept),
                                  prior(normal(0, 1), class = b),
                                  prior(exponential(1), class = sd),
                                  prior(lkj(2), class = cor)),
                        
                        iter = 2000, 
                        warmup = 1000, 
                        chains = 4, 
                        cores = 4,
                        seed = 13,
                        sample_prior = T,
                        control = list(adapt_delta = 0.95),
                        file = here("models/02_model_output/ris_medium_model"))

ris_medium_model <- add_criterion(ris_medium_model, c("loo", "waic"))
```

``` r
ris_full_model <- brm(data = data_samp_samp,
                      family = bernoulli(link = "logit"),
                      
                      afforestation ~
                        slope_z + aspect_z +
                        ORCDRC_z + PHIHOX_z + WWP_z +
                        dist_pop_z +dist_po_mill_z + dist_road_z + dist_afforestation_z +
                        # multilevel terms
                        (1 + slope_z + aspect_z +  ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | MPIO_CNM_1) +
                        (1 + slope_z + aspect_z +  ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | class) +
                        (1 + slope_z + aspect_z +  ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | year) +
                        (1 + slope_z + aspect_z +  ORCDRC_z + PHIHOX_z + WWP_z + dist_pop_z + dist_afforestation_z | Oferta_Amb),
                      
                      prior = c(prior(normal(0, 0.5), class = Intercept),
                                prior(normal(0, 1), class = b),
                                prior(exponential(1), class = sd),
                                prior(lkj(2), class = cor)),
                      
                      iter = 2000, 
                      warmup = 1000, 
                      chains = 4, 
                      cores = 4,
                      seed = 13,
                      sample_prior = T,
                      control = list(adapt_delta = 0.95),
                      file = here("models/02_model_output/ris_full_model"))

ris_full_model <- add_criterion(ris_full_model, c("loo", "waic"))
```

## 4. model comparison

``` r
loo_compare(base_model,
            base_model_no_group,
            base_slim_model,
            ris_slim_model,
            ris_medium_model,
            ris_full_model,
            criterion = "loo") %>% print(simplify = F)
```

    ##                     elpd_diff se_diff elpd_loo se_elpd_loo p_loo  se_p_loo
    ## ris_slim_model         0.0       0.0  -672.5     40.5        63.6    6.4  
    ## ris_medium_model      -3.4       1.4  -675.9     40.9        68.2    6.7  
    ## ris_full_model        -6.9       2.9  -679.4     41.1        81.3    7.6  
    ## base_slim_model      -28.4       9.6  -700.9     41.3        23.5    2.1  
    ## base_model           -31.8       9.7  -704.3     41.5        27.6    2.3  
    ## base_model_no_group -143.4      18.7  -815.9     44.5         8.9    0.9  
    ##                     looic  se_looic
    ## ris_slim_model      1345.0   81.1  
    ## ris_medium_model    1351.9   81.8  
    ## ris_full_model      1358.7   82.2  
    ## base_slim_model     1401.8   82.6  
    ## base_model          1408.5   83.0  
    ## base_model_no_group 1631.8   89.0
