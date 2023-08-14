from plotting import plot; 
from Filtering import ParticleFilter; 
import time; 
from Datagen import DataGenerator; 
import numpy as np


##Run cProfile and snakeviz to extract call stack runtime


def main():
    start = time.time(); 

    def beta(t):
        
      betaMax1=0.1
      theta=0

      return 0.1+betaMax1*(1.0-np.cos(theta+t/7/52*2*np.pi));  
      #return 0.4; 


    params = {"beta":beta,"gamma":0.04,"eta":0.1,"hosp":5.3,"L":4.0,"D":90.0}
    
    initial_state = np.array([100000 ,1000,0])
    time_series = 500; 
    dg = DataGenerator(params,initial_state,time_series,data_name="beta_test",noise=True,hospitalization=False); 

    dg.generate_data(); 
    dg.plot_daily_infected(); 
    dg.plot_beta(); 
    dg.plot_states(); 

#     #HOSPITALIZATION RATE FOR FLU IS 0.01

    pf = ParticleFilter(beta_prior=[0.,1.],
                                  population=101000,
                                  num_particles=1000, 
                                  hyperparamters=[0.01,0.1],
                                  static_parameters=[0.04,0.1],
                                  init_seed_percent=0.01,
                                  filePath="beta_test.csv",
                                  estimate_gamma=False); 
        

    time_series = 499; 
    out = pf.estimate_params(time_series);
    end = time.time();

    print("The time of execution of the program is :",
      (end-start), "s") 

    plot(out,0);  
    plot(out,1);   
    plot(out,2); 



if __name__ == "__main__":
    main()