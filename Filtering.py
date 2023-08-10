import numpy as np; 
import pandas as pd; 
import NumericalPropagator; 
from scipy.stats import poisson;
from scipy.special import gamma; 

class ParticleFilter: 

    def __init__(self,population,beta_prior,num_particles,hyperparamters,filePath,estimate_gamma = False):

        #Particle and weight initialization


        #hyperparameters are sigma1,sigma2 and alpha
        self.particles = []; 
        self.static_parameters = [];
        self.weights = np.ones(shape=num_particles); 
        self.Propagrator = NumericalPropagator.one_step_propagator();
        self.dailyInfected = np.zeros(shape=num_particles); 
        self.gamma = 0.04; 
        self.estimate_gamma = estimate_gamma; 
        self.population = population; 
        self.hyperparameters = hyperparamters;    


        self.weights /= num_particles;  
        

        for i in range(num_particles): 

            initial_infected = np.random.uniform(0,self.population * 0.1); 

            initial_state = [self.population - initial_infected,initial_infected,0]; 

            if(estimate_gamma):
                initial_static_parameters = [np.random.uniform(0,0.1),0.02]; 
            else:

                #0.02 is rate at which people return to S
                initial_static_parameters = [self.gamma,0.02]; 

            beta = (
                np.random.uniform(low=beta_prior[0],
                                  high=beta_prior[1])); 
            

            particle = [initial_state,beta]; 
            self.particles.append(particle); 

            self.static_parameters.append(initial_static_parameters); 

        #Obseravtion data initalization
        self.observation_data = pd.read_csv(filePath); 
        self.observation_data = self.observation_data.to_numpy(); 
        self.observation_data = np.delete(self.observation_data,0,1);


#calls all internal functions to estimate the parameters
    def estimate_params(self,time): 
        betas = np.zeros(shape=(time));
        dI_average = np.zeros(shape=time); 
        qtls = np.empty(shape=(time,23)); 
        betas[0] = (self.average_beta())
        dI_average[0] = (self.average_dI()); 
        for t in range(time): 
            self.propagate(); 
            temp_weights =  self.resample_with_temp_weights(t); 

            self.random_perturbations(); 

            qtls[t] = (self.quantiles()); 

            self.norm_likelihood(temp_weights_old=temp_weights,t=t)

            betas[t] = (self.average_beta());
            dI_average[t] = (self.average_dI()); 
        
            print(f"Iteration:{t} of {time}"); 

        return betas,dI_average,qtls; 

    #internal helper function to propagate the particle cloud
    def propagate(self): 
        for i in range(len(self.particles)): 
                 
                self.Propagrator.params = [self.particles[i][1],self.static_parameters[i][0],self.static_parameters[i][1]];
                self.Propagrator.state = self.particles[i][0]; 
                temp = self.Propagrator.propagate_euler(); 
                self.particles[i][0]= np.array(temp[0]); 
                self.dailyInfected[i] = temp[1]; 

                if(self.estimate_gamma): 
                    self.particles[i][1] = self.particles[i][1] * np.exp(self.hyperparameters[2] * np.random.normal(0,1)); 


    #internal helper function to compute weights based on observations
    def compute_temp_weights(self,t):
        temp_weights = np.ones(len(self.particles)); 
        for j in range(len(self.particles)):    
            temp_weights[j] =  poisson.pmf(np.round(self.observation_data[t+1]),self.dailyInfected[j]);

            #temp_weights[j] = self.weights[j] * (((self.dailyInfected[j])**(np.round(self.observation_data[t+1]))/gamma(np.round(self.observation_data[t+1]))) * np.exp(-self.dailyInfected[j])); 

            if(temp_weights[j] == 0):
                temp_weights[j] = 10**-300; 
            elif(np.isnan(temp_weights[j])):
                temp_weights[j] = 10**-300;
            elif(np.isinf(temp_weights[j])):
                temp_weights[j] = 10**-300;

        temp_weights = temp_weights/sum(temp_weights); 
        

        return temp_weights; 

    #resample based on the temp weights that were computed
    def resample_with_temp_weights(self,t): 

        temp_weights = self.compute_temp_weights(t); 
        indexes = np.zeros(len(self.particles));
        for i in range(len(self.particles)):
            indexes[i] = i;
        new_particle_indexes = np.random.choice(a=indexes, size=len(self.particles), replace=True, p=temp_weights);

        for i in range(len(self.particles)):
            self.particles[i] = self.particles[int(new_particle_indexes[i])];

        return temp_weights;  
    
    #applies the geometric random walk to the particles
    def random_perturbations(self):

        #sigma1 is the deviation of the state and sigma2 is the deviation of beta
        sigma1 = self.hyperparameters[0]; 
        sigma2 = self.hyperparameters[1]; 
        
        #for fixed beta use 0.4 and for variable use 0.014 
        C = np.array([[((sigma1)**2)/self.population,0,0,0],
                      [0,(sigma1)**2,0,0],
                      [0,0,(sigma1)**2,0],
                      [0,0,0,(sigma2)**2],
        ]); 
        
        
        for i in range(len(self.particles)):
            temp = []; 
            for  j in range(len(self.particles[i][0])):
                temp.append(self.particles[i][0][j]); 
    
            temp.append(self.particles[i][1]); 
    
            temp = np.log(temp); 
            perturbed = np.random.multivariate_normal(mean = temp,cov = C);
            perturbed = np.exp(perturbed); 
            s = (np.sum(perturbed[0:3]));
            perturbed[0:3]= (perturbed[0:3] / s) * self.population; 
            self.particles[i] = [perturbed[0:3],perturbed[3]];
            
    #computes the normalized likelihood
    def norm_likelihood(self,temp_weights_old,t):
        temp_weights = np.zeros(len(self.particles)); 
        for j in range(len(self.particles)): 
            temp_weights[j] = poisson.pmf(np.round(self.observation_data[t+1]),self.dailyInfected[j]);

        temp_weights /= sum(temp_weights);
    
        for j in range(len(self.particles)):
            self.weights[j] = temp_weights[j]/temp_weights_old[j]; 

    
    #function to print the particles in a human readable format
    def print_particles(self):
        for i in range(len(self.particles)): 
            print(self.particles[i]); 

    #average beta helper function
    def average_beta(self): 
        mean = 0;
        for i in range(len(self.particles)):
            mean += self.particles[i][1]; 
        mean /= len(self.particles);
        return(mean);

    #average betaSI\N helper function
    def average_dI(self): 
        return np.mean(self.dailyInfected); 

    def quantiles(self): 
        qtlMark = 1.00*np.array([0.010, 0.025, 0.050, 0.100, 0.150, 0.200, 0.250, 0.300, 0.350, 0.400, 0.450, 0.500, 0.550, 0.600, 0.650, 0.700, 0.750, 0.800, 0.850, 0.900, 0.950, 0.975, 0.990]);
        return np.quantile(self.dailyInfected, qtlMark);




















                 







