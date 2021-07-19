# http://www.jeremy-oakley.staff.shef.ac.uk/mas61004/EDAtutorial/eda-for-logistic-regression.html
# load_packages -----------------------------------------------------------
pacman::p_load(vroom, here,
               tidyverse,hrbrthemes,viridis, 
               bayesplot,rstanarm,
               HSAUR3)

# config ------------------------------------------------------------------
theme_set(bayesplot::theme_default())
# load_data ---------------------------------------------------------------
data <- vroom(here("data/03_processed/sample_points/sample_points_0624.csv")) # one could also check out feather 
#data_ <- read.csv(here ("data/03_processed/sample_points/sample_points_0624.csv"))
data("womensrole", package = "HSAUR3")
#data$year = lubridate::ymd(data$year, truncated = 2L)

#cbind(womensrole$agree, womensrole$disagree)

#data_geo <- readOGR(here ("data","df_lc_change_veg_areas_geom.gpkg"), "df_lc_change_veg_areas_geom")
#data_geo$year = lubridate::ymd(data_geo$year, truncated = 2L)

#outname <- "df_lc_change_veg_areas_geom_time.gpkg"
#writeOGR(data_geo, dsn = outname, layer = "df_lc_change_veg_areas_geom_time", driver = "GPKG")


# tidy data ---------------------------------------------------------------
# remove all class == 50 as we are not interested in forest class as predictor
data<-data[!(data$class==50),]
# remove all year == 2003 as we do not have dist_afforastation in that year
data<-data[!(data$year==2003),]
data<-data[!(data$year==2019),]

# remove all neigh_tot != 9 as we want points with full neighbourhood
#data<-data[!(data$neigh_tot!=9),]
#data<-data[!(data$neigh_tot<=8),]
#data<-data[!(data$neigh_tot<=7),]
data<-data[!(data$neigh_tot<=6),]
#data<-data[!(data$neigh_tot<=5),]
sum(data$afforestation)/nrow(data)

sum(data$year==2015) # there is not afforestation taking place in 14/15, which is why dist_afforestation is nan in all 2015 entries

# remove uncessary columns
data <- data[, !(colnames(data) %in% c("...1","x","y", "count", "count_forest"))]


# data types
sapply(data, typeof)
# categorical values
# class, MPIO_CNM_1
data$class <- as.factor(data$class)
data$MPIO_CNM_1 <- as.factor(data$MPIO_CNM_1)
data$plot_id <- as.factor(data$plot_id)
#data$afforestation <- as.factor(data$afforestation)

# standarization
data <- data %>% mutate_at(c("altitude","slope","curvature","aspect",
                             "AWcTS","WWP","ORCDRC","PHIHOX",
                             "dist_pop","dist_river","dist_po_mill","dist_afforestation"), ~(scale(.)))
# outliers

# sampling




# Investigating the experimental design -----------------------------------
levels(data$class)
levels(data$plot_id)
levels(factor(data$afforestation))
levels(data$MPIO_CNM_1)

data %>% 
  count(plot_id,class, MPIO_CNM_1) %>%
  pull(n) %>%
  summary()


# Contingency tables ------------------------------------------------------
xtabs( ~ class + factor(afforestation), data = data)
xtabs( ~ MPIO_CNM_1 + factor(afforestation), data = data)
xtabs( ~ plot_id + factor(afforestation), data = data)
# Checking for identical responses ----------------------------------------
data %>%
  group_by(MPIO_CNM_1, class) %>%
  summarise(proportion  = mean(afforestation), .groups = 'drop') 

xtabs(afforestation ~ MPIO_CNM_1 + class, data = data)

data %>% 
  group_by(plot_id) %>%
  summarise(meanStable = mean(afforestation), .groups = 'drop') %>%
  count(meanStable) 

# Exploratory plots -------------------------------------------------------
ggplot(data, aes(x = factor(afforestation), y = dist_afforestation)) + 
  geom_boxplot()

ggplot(data, aes(x = factor(afforestation), y = dist_afforestation,
                 colour = MPIO_CNM_1)) + 
  geom_boxplot()

ggplot(data, aes(x = MPIO_CNM_1, y = dist_afforestation,
                 colour = factor(afforestation))) + 
  geom_boxplot()


p1 <- ggplot(data, aes(x = MPIO_CNM_1, y = dist_afforestation,
                          colour = factor(afforestation))) + 
  geom_boxplot()
p2 <- ggplot(data, aes(x = MPIO_CNM_1, y = dist_pop ,
                          colour = factor(afforestation))) + 
  geom_boxplot()

p3 <- ggplot(data, aes(x = MPIO_CNM_1, y = dist_river,
                          colour = factor(afforestation))) + 
  geom_boxplot()

p4 <- ggplot(data, aes(x = MPIO_CNM_1, y = dist_po_mill,
                          colour = factor(afforestation))) + 
  geom_boxplot()

gridExtra::grid.arrange(p1, p2, p3,p4,  ncol = 2)
# Plotting mean proportions -----------------------------------------------
dataGrouped <- data %>% 
  group_by(plot_id) %>%
  summarise(proportionAfforest = mean(afforestation),
            MPIO_CNM_1 = MPIO_CNM_1[1],
            dist_afforestation = dist_afforestation[1],
            .groups = 'drop')
head(dataGrouped)


ggplot(dataGrouped, aes(x = dist_afforestation, y = proportionAfforest,
                           col = MPIO_CNM_1))+
  geom_point() 
