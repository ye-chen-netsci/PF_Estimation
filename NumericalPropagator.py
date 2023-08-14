#The numerical propagator to go from time t to t+1

import numpy as np; 


class one_step_propagator: 
    state: list
    params: list

    def __init__(self): 
        self.state = list();
        self.params = list(); 

    def RHS(self,state,params):
    #params has all the parameters – beta, gamma
    #state is a numpy array

        S,I,R = state;
        N = S + I + R; 

        new_I = params[0]*S*I/N;

        dS = -params[0]*(S*I)/N + params[2] * R
        dI = params[0]*S*I/N-params[1]*I
        dR = params[1]*I - params[2] * R; 



        return np.array([dS,dI,dR]),new_I

    def propagate_euler(self):
         #define time step of Euler's method

        NperDay = 1
        sol = np.zeros((3, NperDay+1))
        tSpanFine = np.linspace(0, 1, NperDay+1)

        dailyInfected = 0;

        #initiate the values of SIR compartments at the first time point
        sol[:,0] = np.array([self.state[0], self.state[1], self.state[2]])

        for i in range(len(tSpanFine)-1):

            dt,new_I = self.RHS(sol[:,i],self.params)
            dailyInfected =  new_I/NperDay;
            sol[:,i+1] = sol[:,i] + dt/NperDay;
        
        return sol[:,-1],dailyInfected;









    def RHS_H(self,state,params):
    #params has all the parameters – beta, gamma
    #state is a numpy array

        S,I,R,H = state;
        N = S + I + R + H; 

        beta,L,D,gamma,hosp = params; 

        dS = -beta*(S*I)/N + (1/L)*R; 

        dI = beta*S*I/N-(1/D)*I;

        dR = (1/hosp) * H + ((1/D)*(1-gamma)*I)-(1/L)*R; 

        dH = ((1/D)*gamma) * I - (1/hosp) * H; 

        return np.array([dS,dI,dR,dH])

    def propagate_euler_H(self):
         #define time step of Euler's method

        NperDay = 1
        sol = np.zeros((4, NperDay+1))
        tSpanFine = np.linspace(0, 1, NperDay+1)

        #initiate the values of SIR compartments at the first time point
        sol[:,0] = np.array([self.state[0], self.state[1], self.state[2],self.state[3]])

        for i in range(len(tSpanFine)-1):

            dt = self.RHS(sol[:,i],self.params)
            sol[:,i+1] = sol[:,i] + dt/NperDay;
        
        return sol[:,-1];


