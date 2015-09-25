from django.db import models
from Factz.utils import rand_code, format_number
from Factz.messaging import send_test_message, send_message
from django.utils import timezone
from datetime import datetime
from time import sleep

class Variable(models.Model):
    name = models.CharField(max_length=64, unique=True)
    val = models.CharField(max_length=128)
    
    def __str__(self):
        return self.name + "=" + self.val
    
class Subscription(models.Model):
    name = models.CharField(max_length=16, unique=True)
    active = models.BooleanField(default=True)
    count = models.IntegerField(default=0)
    last_sent = models.DateTimeField(null=True, blank=True)
    next_send = models.DateTimeField(null=True, blank=True)
    inserted_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    #Revamp: add end_time and auto-caluclate send_delay
    send_base = models.TimeField(default=datetime(1,1,1,16))
    send_delay = models.PositiveIntegerField(default=465)

    #Could we use a text field with validation instead?
    send_monday = models.BooleanField(default=True)
    send_tuesday = models.BooleanField(default=True)
    send_wednesday = models.BooleanField(default=True)
    send_thursday = models.BooleanField(default=True)
    send_friday = models.BooleanField(default=True)
    send_saturday = models.BooleanField(default=True)
    send_sunday = models.BooleanField(default=True)
    
    def wait_seconds(self):
        val = self.send_delay*60
        return(val)
    
    def start_time(self):
        hours = self.send_base.hour
        minutes = self.send_base.minute
        val = (hours*60+minutes)*60
        return(val)
    
    def check_today(self):
        today = datetime.today().weekday()
        if today == 0:
            val = self.send_monday
        elif today == 1:
            val = self.send_tuesday
        elif today == 2:
            val = self.send_wednesday
        elif today == 3:
            val = self.send_thursday
        elif today == 4:
            val = self.send_friday
        elif today == 5:
            val = self.send_saturday
        elif today == 6:
            val = self.send_sunday
        return(val)

    def update_sent(self):
        self.last_sent = timezone.now()
        self.count += 1
        self.save()
        
    def __str__(self):
        return self.name

class Message(models.Model):
    sheet_id = models.IntegerField()
    message = models.CharField(max_length=320)
    follow_up = models.CharField(max_length=160, blank=True, null=True)
    source = models.CharField(max_length=160, blank=True, null=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    count = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    inserted_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def update_sent(self):
        self.count += 1
        self.last_sent = timezone.now()
        self.save()
    
    def __str__(self):
        return self.message
        
    class Meta:
        unique_together = ('sheet_id', 'subscription')

class Number(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    confirmation_code = models.CharField(max_length=6, default=rand_code)
    message_cnt = models.IntegerField(default=0)
    confirmed = models.BooleanField(default=False)
    last_sent = models.DateTimeField(null=True, blank=True)
    inserted_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def update_sent(self):
        self.last_sent = timezone.now()
        self.message_cnt += 1
        self.save()
    
    def create(self, *args, **kwargs):
        self.phone_number = format_number(self.phone_number)
        
        chk = send_test_message(self)
        if chk[0] != 0:
            raise ValueError(chk[1])
		
    def __str__(self):
        return self.phone_number
        
class activeSubscription(models.Model):
    number = models.ForeignKey(Number, on_delete=models.PROTECT)
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    message = models.ForeignKey(Message, blank=True, null=True, default=None, on_delete=models.SET_NULL)
    message_cnt = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    inserted_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def update_sent(self, msgObj):
        self.message = msgObj
        self.message_cnt += 1
        self.last_sent = timezone.now()
        self.number.update_sent()
        self.save()
    
    def send(self, msgObj):
        if self.active == True:
            res = send_message(msgObj, self)
            if res[0] == 0:
                self.update_sent(msgObj)
                if msgObj.follow_up not in ('', None):
                    sleep(1)
                    f_res = send_message(msgObj, self, type="followup")
                else:
                    f_res = (-2, "No follow up.")
            else:
                f_res = (4, "Message failed, did not attempt.")
        else:
            res = (-1, "Not active.")
            f_res = res
        return {"Message":res, "Followup":f_res}
    
    class Meta:
        unique_together = ('number', 'subscription')
    
    def __str__(self):
        return str(self.number) + " " + str(self.subscription) + " (" + str(self.active) + ")"
