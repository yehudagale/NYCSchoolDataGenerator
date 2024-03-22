from heapq import heappushpop, heappush, heappop
from abc import ABC, abstractmethod
#This represents one actor in the gale shapley exchange
#Converts the id of a school/student to its object, make sure the thing you are using as names are unique (i.e. student ids)
ID_TO_OBJECT = {}
class Actor(ABC):
    """docstring for Actor"""
    def __init__(self, id, preferences):
        #Unique identifier
        self.id = id
        #prefence list of id's
        self.prefs = preferences
        #dictionary that lets us quickly find actors in preference list
        self.pref_dict = {pref:i for i,pref in enumerate(preferences)}
    #return True if this actor wants to match with actor_2 otherwise false
    @abstractmethod
    def check_proposal(self, actor_2):
        return False
    #matches this actor to actor_2
    @abstractmethod
    def add_match(self, actor_2):
        pass
    #we propose to actor_2
    def propose(self, actor_2):
        if actor_2.check_proposal(self):
            my_old_match = self.add_match(actor_2)
            other_old_match = actor_2.add_match(self)
            if my_old_match:
                my_old_match.add_match(None)
            if other_old_match:
                other_old_match.add_match(None)
            return (my_old_match, other_old_match)
        return ()
    def __str__(self):
        return str(self.id)
    def __eq__(self, other):
        if other is None:
            return False
        # if not other:
            # return False
        # print(self, other)
        return other.id == self.id

class Single_Slot(Actor):
    """Actor with only one slot e.g. student, man/women in the marriage case"""
    def __init__(self, id, preferences):
        super(Single_Slot, self).__init__(id, preferences)
        #the actor you are currently matched to
        self.current_match = None
        #how far down your preference list you are
        self.preference_slot = 0
    #switches your current match with actor_2
    def add_match(self, actor_2):
        temp = self.current_match
        self.current_match = actor_2
        return temp
    #propose to actors on your preference list until you get matched or finish your preference list
    def propose_until_matched(self):
        if self.preference_slot == -1:
            return None

        global ID_TO_OBJECT
        if self.current_match:
            raise ValueError
        #will hold the previous matches
        old_items = ()
        while not old_items:
            if self.preference_slot == len(self.prefs):
                # Denote exhausted self.prefs without finding a match
                self.preference_slot = -1
                return None
            old_items = self.propose(ID_TO_OBJECT[self.prefs[self.preference_slot]])
            self.preference_slot += 1
        # Return other_old_match to signify what was unmatched to match self
        return old_items[1]
    def check_proposal(self, actor_2):
        if self.current_match is None:
            return True
        return self.pref_dict.get(actor_2.id, len(self.pref_dict)) < self.pref_dict.get(self.current_match.id, len(self.pref_dict))
class Multi_Slot(Actor):
    """docstring for Multi_Slot"""
    def __init__(self, id, preferences, capacity, record_applicants=False):
        super(Multi_Slot, self).__init__(id, preferences)
        self.current_match = []
        self.capacity = capacity
        self.record_applicants = record_applicants
        if record_applicants:
            self.proposed = []

    def add_match(self, actor_2):
        if self.capacity > len(self.current_match):
            heappush(self.current_match, (len(self.pref_dict) - self.pref_dict[actor_2.id], actor_2))
            return None
        return heappushpop(self.current_match, (len(self.pref_dict) - self.pref_dict[actor_2.id], actor_2))[1]
    def get_match(self):
        return [(self.pref_dict[item[1].id], item[1].id) for item in self.current_match]
    def check_proposal(self, actor_2):
        # if verbose:
        #     print(f'actor 2 priority {self.pref_dict.get(actor_2.id,len(self.pref_dict))}')
        #     print(f'current num_items {len(self.current_match)}')
        #     print(f'current worst priority {self.pref_dict.get(self.current_match[0][1].id,len(self.pref_dict))}')
        #     print(f'pref dict length is {len(self.pref_dict)}')
        if self.record_applicants:
            self.proposed.append((self.pref_dict.get(actor_2.id, len(self.pref_dict)), actor_2))
        if self.capacity <= 0:
            return False
        elif self.pref_dict.get(actor_2.id) is None:
            return False
        elif len(self.current_match) < self.capacity:
            return True
        else:
            return self.pref_dict.get(actor_2.id,len(self.pref_dict)) < self.pref_dict.get(self.current_match[0][1].id,len(self.pref_dict))

class Quota_Multi(Multi_Slot):
    def __init__(self, goal_percent, ID, preferences, capacity, quota_dict):
        super(Quota_Multi, self).__init__(ID, preferences, capacity)
        self.quota = round(self.capacity * goal_percent)
        self.protected_heap = []
        # self.proposed = []
        self.quota_dict = quota_dict
        #note that current match will only hold unprotected items
        # self.protected_count = 0
        # self.protected_pref_dict = {pref:i - (len(preferences) * quota_dict[pref])  for i,pref in enumerate(preferences)}
    def add_match(self, actor_2):
        #either way, the item will need to be pushed onto the correct heap
        if self.quota_dict[actor_2.id]:
            heappush(self.protected_heap, (len(self.pref_dict) - self.pref_dict[actor_2.id], actor_2))
        else:
            heappush(self.current_match, (len(self.pref_dict) - self.pref_dict[actor_2.id], actor_2))
        #If I have room, I'm done
        if self.capacity >= len(self.current_match) + len(self.protected_heap):
            return None

        # if I have not met my quota, I never want to remove any items from the protected heap pop the worst unprotected item
        #also do this if the protected heap is empty
        if (len(self.protected_heap) <= self.quota) or len(self.protected_heap) == 0:
            return heappop(self.current_match)[1]
        # If the unprotected heap is empty, remove from the protected_heap
        if len(self.current_match) == 0:
            return heappop(self.protected_heap)[1]
        #in any other regular case remove from the heap that has the lowest value
        #(breaking ties in favor of the protect heap (though in theory ties should not be allowed in dataset))
        if self.protected_heap[0][0] < self.current_match[0][0]:
            if len(self.protected_heap) == self.quota:
                print(self.protected_heap, actor_2.id, self.quota_dict[actor_2.id])
                raise(ValueError)
            return heappop(self.protected_heap)[1]
        else:
            return heappop(self.current_match)[1]
    def check_proposal(self, actor_2):
        # self.proposed.append((actor_2.id, self.quota_dict[actor_2.id]))
        if self.capacity <= 0:
            return False
        elif self.pref_dict.get(actor_2.id) is None:
            return False
        elif len(self.current_match) + len(self.protected_heap) < self.capacity:
            return True
        #Check if item is top "quota" protected items
        if len(self.protected_heap) < self.quota:
            #If I don't yet have "quota" protected items always take a protected item
            if self.quota_dict[actor_2.id]:
                    return True

        #Check if item is in top "capacity" overall items
        #If either heap is empty, only compare to the other one heap
        my_value = len(self.pref_dict) - self.pref_dict.get(actor_2.id,len(self.pref_dict))
        if len(self.current_match) == 0:
            return my_value > self.protected_heap[0][0]
        #If I don't yet meet the quota, I cannot afford to lose any protected items, but can still take an unprotected item if it beats another unprotected item
        #note the or equal to, if I have met my quota exactly I still can't afford to take an unprotected item that kicks out a protected one
        elif len(self.protected_heap) == 0 or (len(self.protected_heap) <= self.quota and not self.quota_dict[actor_2.id]):
            return my_value > self.current_match[0][0]
        else:
            return  my_value > self.current_match[0][0] or my_value > self.protected_heap[0][0]

def gale_shapley_algorithm(students, schools):
    global ID_TO_OBJECT
    ID_TO_OBJECT = {actor.id: actor for actor in students + schools}
    unmatched = students.copy()
    unmatched = [student for student in unmatched if student.preference_slot == 0]
    while unmatched:
        student = unmatched.pop()
        old = student.propose_until_matched()
        if old is not None:
            unmatched.append(old)

    return students, schools

def gale_shapley_algorithm_expand(students, schools, displaced):
    global ID_TO_OBJECT
    ID_TO_OBJECT = {actor.id: actor for actor in students + schools}
    unmatched = students.copy()
    unmatched_displaced = [student for student in unmatched if student.preference_slot == 0 and student.id in displaced]
    unmatched = [student for student in unmatched if student.preference_slot == 0 and student.id not in displaced]
    while unmatched:
        student = unmatched.pop()
        old = student.propose_until_matched()
        if old is not None:
            unmatched.append(old)
    # print(displaced)
    while unmatched_displaced:
        # print("here")
        student = unmatched_displaced.pop()
        old = student.propose_until_matched()
        if old is not None:
            unmatched_displaced.append(old)
    return students, schools


if __name__ == '__main__':
    students = []
    schools = []
    # schools.append(TTC_Multi_Slot('S1', ['I1', 'I2', 'I3', 'I4', 'I5', 'I6', 'I7', 'I8'], 2))
    # schools.append(TTC_Multi_Slot('S2', ['I3', 'I5', 'I4', 'I8', 'I7', 'I2', 'I1', 'I6'], 2))
    # schools.append(TTC_Multi_Slot('S3', ['I5', 'I3', 'I1', 'I7', 'I2', 'I8', 'I6', 'I4'], 3))
    # schools.append(TTC_Multi_Slot('S4', ['I6', 'I8', 'I7', 'I4', 'I2', 'I3', 'I5', 'I1'], 3))
    #
    students.append(Single_Slot('A', ['Blue', 'Red', 'Yellow']))
    students.append(Single_Slot('B', ['Red', 'Blue', 'Yellow']))
    students.append(Single_Slot('C', ['Blue', 'Red', 'Yellow']))
    # students.append(TTC_Single_Slot('I4', ['S3', 'S4', 'S1', 'S2']))
    # students.append(TTC_Single_Slot('I5', ['S1', 'S3', 'S4', 'S2']))
    # students.append(TTC_Single_Slot('I6', ['S4', 'S1', 'S2', 'S3']))
    # students.append(TTC_Single_Slot('I7', ['S1', 'S2', 'S3', 'S4']))
    # students.append(TTC_Single_Slot('I8', ['S1', 'S2', 'S4', 'S3']))
    schools.append(Multi_Slot('Red', ['A', 'C', 'B'], 1))
    schools.append(Multi_Slot('Yellow', ['A', 'B', 'C'], 1))
    schools.append(Multi_Slot('Blue', ['B', 'C', 'A'], 1))

    gale_shapley_algorithm(students, schools)
    for student in students:
        print(f'id: {student.id}, school: {student.current_match.id}')
