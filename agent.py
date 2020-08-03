from keras import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import Adam
import random 
import math
import numpy as np
from stats import *
from config import *

class DQN():
    def __init__(self):
        self.model = self.create_model()

    def create_model(self):
        model = Sequential()
        model.add(Dense(L1, input_shape=(STATE_L,), activation='relu'))
        #model.add(Dropout(.2))
        model.add(Dense(L2, activation='relu'))
        #model.add(Dropout(.2))
        model.add(Dense(L3, activation='relu'))
        #model.add(Dropout(.2))
        model.add(Dense(4))

        model.compile(loss='mse', optimizer=Adam(learning_rate=LR), metrics=['accuracy'])
        model.summary()
        #print('\n\n')
        return model
    
class ReplayMemory():
    def __init__(self, model):
        self.model = model
        self.capacity = CAPACITY
        self.memory = []
        self.push_count = 0
        self.batch_size = BATCH
    
    def push(self, experience):
        if len(self.memory) < self.capacity:
            # Start achieving memory from experience
            self.memory.append(experience)
        else:
            # Progressively replace the acquired experience
            # with fresher one
            self.memory[self.push_count % self.capacity] = experience
        self.push_count += 1
    
    def sample(self):
        # Randomly sample memory
        return random.sample(self.memory, self.batch_size)

    def replay(self, stop):
        if len(self.memory) >= self.batch_size:
            batch = self.sample()
        else:
            batch = self.memory
        
        
        state, act, reward, nxt_state = batch[0]
        nxt_state = np.reshape(nxt_state, (1,STATE_L))
        state = np.reshape(state, (1,STATE_L))
        reward = np.asarray(reward)
        act = np.asarray(act)

        if len(batch)>1:
            for state1, act1, reward1, nxt_state1 in batch[1:]:
                nxt_state1 = np.reshape(nxt_state1, (1,STATE_L))              
                nxt_state = np.vstack((nxt_state, nxt_state1))

                reward1 = np.asarray(reward1)
                reward = np.vstack((reward, reward1))

                state1 = np.reshape(state1, (1,STATE_L))
                state = np.vstack((state, state1))

                act1 = np.asarray(act1)
                act = np.vstack((act, act1))
        q_opt = reward
        
        if not stop:
            q_prime = self.model.predict(nxt_state)
            #print(f"Q': {q_prime}")
            max_q_prime = np.amax(q_prime, axis=1)
            #print(f"max Q': {max_q_prime}")
            max_q_prime = np.reshape(max_q_prime, (q_prime.shape[0],1))
            #print(f"max Q': {max_q_prime}")
            q_opt = np.add(reward, GAMMA * max_q_prime)
            #print(f"Q*: {q_opt}")
        target = self.model.predict(state)
        #target = np.reshape(target, (1, 4))
        #print(F'Target:{target}, Act: {act}')
        try:
            for i in range(act.shape[0]):
                target[i, int(act[i])] = q_opt[i]
        except IndexError:
            target[0, int(act)] = q_opt
        ##print(f'State: {state}')
        ##print(f'Q*: {q_opt}')
        #print(target)
        history = self.model.fit(state, target, epochs=1, verbose=0, batch_size=state.shape[0])
        
        return history.history
        
    
    def exploit(self, state):
        state = np.reshape(state, (1,STATE_L))  
        ##print(state)
        pred = self.model.predict(state)[0]
        ##print(pred)
        best_act = np.argmax(pred)
        #print(pred, best_act)
        return  best_act

    

class Agent():
    def __init__(self):
        self.model = DQN().model
        self.memory = ReplayMemory(self.model)

    def getState(self, snake, food):
        """
        OB_R, OB_L, OB_F, 
        FOOD_R, FOOD_L, FOOD_U, FOOD_D
        DIR_D, DIR_U, DIR_R, DIR_L
        """
        state = np.zeros(STATE_L, dtype=int)

        # Snake goes down
        if snake.dir == 0:
            state[7] = True
            # Obstacle Right
            head = (snake.x[0]-20 , snake.y[0])
            for i in range(1, snake.len):
                if head == (snake.x[i], snake.y[i]) or head[0] < 10: 
                    state[0] = True
                    break
            # Obstacle Left
            head = (snake.x[0]+20 , snake.y[0])
            for i in range(1, snake.len):
                #if head == (snake.x[i], snake.y[i]) or head[0] > 580:
                if head == (snake.x[i], snake.y[i]) or head[0] > W-40: 
                    state[1] = True
                    break
            # Obstacle Forward
            head = (snake.x[0] , snake.y[0]+20)
            for i in range(1, snake.len):
                #if head == (snake.x[i], snake.y[i]) or head[1] > 580: 
                if head == (snake.x[i], snake.y[i]) or head[0] > H-40:
                    state[2] = True
                    break
            
        # Snake goes Up
        if snake.dir == 2:
            state[8] = True
            # Obstacle Right
            head = (snake.x[0]+20 , snake.y[0])
            for i in range(1, snake.len):
                #if head == (snake.x[i], snake.y[i]) or head[0] > 580: 
                if head == (snake.x[i], snake.y[i]) or head[0] > W-40: 
                    state[0] = True
                    break
            # Obstacle Left
            head = (snake.x[0]-20 , snake.y[0])
            for i in range(1, snake.len):
                if head == (snake.x[i], snake.y[i]) or head[0] < 10: 
                    state[1] = True
                    break
            # Obstacle Forward
            head = (snake.x[0] , snake.y[0]-20)
            for i in range(1, snake.len):
                if head == (snake.x[i], snake.y[i]) or head[1] < 10: 
                    state[2] = True
                    break
            
        # Snake goes Right
        if snake.dir == 1:
            state[9] = True
            # Obstacle Right
            head = (snake.x[0] , snake.y[0]+20)
            for i in range(1, snake.len):
                #if head == (snake.x[i], snake.y[i]) or head[1] > 580: 
                if head == (snake.x[i], snake.y[i]) or head[0] > H-40:
                    state[0] = True
                    break
            # Obstacle Left
            head = (snake.x[0] , snake.y[0]-20)
            for i in range(1, snake.len):
                if head == (snake.x[i], snake.y[i]) or head[1] < 10: 
                    state[1] = True
                    break
            # Obstacle Forward
            head = (snake.x[0]+20 , snake.y[0])
            for i in range(1, snake.len):
                #if head == (snake.x[i], snake.y[i]) or head[0] > 580: 
                if head == (snake.x[i], snake.y[i]) or head[0] > W-40: 
                    state[2] = True
                    break
        
        # Snake goes Left
        if snake.dir == 3:
            state[10] = True
            # Obstacle Right
            head = (snake.x[0] , snake.y[0]-20)
            for i in range(1, snake.len):
                if head == (snake.x[i], snake.y[i]) or head[1] < 10: 
                    state[0] = True
                    break
            # Obstacle Left
            head = (snake.x[0] , snake.y[0]+20)
            for i in range(1, snake.len):
                #if head == (snake.x[i], snake.y[i]) or head[1] > 580: 
                if head == (snake.x[i], snake.y[i]) or head[0] > H-40:
                    state[1] = True
                    break
            # Obstacle Forward
            head = (snake.x[0]-20 , snake.y[0])
            for i in range(1, snake.len):
                if head == (snake.x[i], snake.y[i]) or head[0] < 10: 
                    state[2] = True
                    break

        # Food position wrt head            
        state[3] = int(snake.x[0]<food.pos[0])  # Food Right
        state[4] = int(snake.x[0]>food.pos[0])  # Food Left
        state[5] = int(snake.y[0]>food.pos[1])  # Food Up
        state[6] = int(snake.y[0]<food.pos[1])  # Food Down
        """
        dist = snake.x[0]-food.pos[0]
        state[3] = dist

        dist = -snake.x[0]+food.pos[0]
        state[4] = dist

        dist = snake.y[0]-food.pos[1]
        state[5] = dist

        dist = -snake.y[0]+food.pos[1]
        state[6] = dist
        """
        # FOOD distance wrt head
        dist = np.sqrt((snake.x[0]-food.pos[0])**2 + (snake.y[0]-food.pos[1])**2)
        #state[11] = dist
        """
        # Snake ate or crashed
        state[12] = snake.ate
        state[13] = snake.crashed
        """
        return state 
    
    def getEpsilon(self, current_step):
        eps = END + (START - END)*math.exp(-1*current_step*DECAY)

        return eps

    def setReward(self, died, ate, state):
        reward = 0
        if died: 
            reward = DIED
        elif ate: 
            reward = ATE
        else:
            reward = -1
            """
            if state[11] != 0:
                reward -= 1.0/state[11]*10
            else:
                reward = -0.000000001
            """
        ##print(reward)

        return reward
    