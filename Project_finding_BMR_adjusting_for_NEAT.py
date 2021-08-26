# -*- coding: utf-8 -*-
"""
Created on Thu Aug 26 10:17:46 2021

@author: omar_
"""

#My question was on why docters says that i would need to eat 2500 calories
#every day. I found out that our body burns calories within itself just
# to make organs, muscles etc to fucntion, but no doctor told me that.

#goal is to create a clas were we calc a person basic metabolic rate(BMR)
# as well as adjsuting for non exercise activity thermogenesis (NEAT)
# in order to figure out how much a person should consume.

class BmrCalculations(object):
    def __init__(self, weight_in_kg ,height_in_cm,age_in_years,gender,activity):
        self.weight = weight_in_kg
        self.height = height_in_cm
        self.age = age_in_years
        self.gender = gender.upper()
        self.activity = str(activity)
        self.BMR()
        self.BMR_Adjusted()
        
        
        print(f'BMR = {self.bmr} and the BMR Adjsuted = {self.adjusted}')
        



        
    def BMR(self):
        if self.gender == 'MAN':
            self.bmr = 10*self.weight + 6.25 * self.height - 5 * self.age + 5
            return self.bmr
        else:
            if self.gender == 'WOMAN':
                self.bmr = 10*self.weight + 6.25 * self.height - 5 * self.age - 161
                return self.bmr
            
    def BMR_Adjusted(self):
        dic = {'1': 1.35, '2': 1.65,'3':1.9,'4':2.1}
        if self.activity == '1':
            self.adjusted = self.bmr * dic[self.activity]
            return self.adjusted 
        if self.activity == '2':
            self.adjusted = self.bmr * dic[self.activity]
            return self.adjusted
        if self.activity == '3':
            self.adjusted = self.bmr * dic[self.activity]
            return self.adjusted
        if self.activity == '4':
            self.adjusted = self.bmr * dic[self.activity]
            return self.adjusted      
        
    
        
#can refine this one.
                

omar = BmrCalculations(73,180,23,'man',1)
