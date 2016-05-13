from Uncertainties import measurement
from Uncertainties import function
from Uncertainties import constant
#from math import pi
CONSTANT = (int,float,)

def error(*args,der=None):
    std=0
    roots=()
    for arg in args:
        for i in range(len(arg.root)):
            if arg.root[i] not in roots:
                roots+=(arg.root[i],)
    for root in roots:
        std+=(der[root]*measurement.register[root].std)**2
    for i in range(len(roots)):
        for j in range(len(roots)-i-1):
            cov=measurement.register[roots[i]]\
                    .get_covariance(measurement.register[roots[j+1+i]])
            std+=2*der[roots[i]]*der[roots[j+1+i]]*cov
    std=std**(1/2)
    return std;
    
def check_values(*args):
    '''
    Checks that the arguments are measurement type, otherwise a measurement
    is returned.
    
    All returned values are of measurement type, if values need to be 
    converted, this is done by calling the normalize function, which
    outputs a measurement object with no standard deviation.
    '''
    val=()
    for arg in args:
        if type(arg) in CONSTANT:
            val+=(constant(arg),)
        else:
            val+=(arg,)
    return val

def check_formula(operation,a,b=None,func_flag=False):
    '''
    Checks if quantity being calculated is already in memory
    
    Using the formula string created for each operation as a key, the
    register of previously calculated operations is checked. If the
    quantity does exist, the previously calculated object is returned.
    '''
    if func_flag is False:
        if a.info["Formula"]+operation+b.info["Formula"] in \
                measurement.formula_register:
            ID = measurement.formula_register[a.info["Formula"]+operation\
                    + b.info["Formula"]]
            return measurement.register[ID]
    else:
        if operation+'('+a.info["Formula"]+')' in measurement.formula_register:
            ID = measurement.formula_register[operation+'('+a.info["Formula"]\
                    + ')']
            return measurement.register[ID]

def add(a,b):
    '''
    Returns a measurement object that is the sum of two other measurements.
    
    The sum can be taken by multiple methods, specified by the measurement
    class variable measurement.method. The derivative of this new object is
    also specifed by applying the chain rule to the input and the 
    derivative of the inputs.
    '''
    a,b=check_values(a,b)
    #Propagating derivative of arguments    
    first_der={}
    a.check_der(b)
    b.check_der(a)
    for key in a.first_der:
        first_der[key]=a.first_der[key]+b.first_der[key]
    if check_formula('+',a,b) is not None:
        return check_formula('+',a,b)
    #Addition by error propogation formula
    if measurement.method=="Derivative":  
        mean=a.mean+b.mean     
        std=error(a,b,der=first_der)
        result=function(mean,std)
        
    #Addition by Min-Max method
    elif measurement.method=="Min Max":
        mean=a.mean+b.mean
        std=a.std+b.std
        result=function(mean,std)
        
    #If method specification is bad, MC method is used
    else:
        plus=lambda x,y: x+y
        result=measurement.monte_carlo(plus,a,b)
    if a.info["Data"] is not None and b.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.add(a.info["Data"],b.info["Data"])
    result.first_der.update(first_der)
    result._update_info('+',a,b)
    return result;

def sub(a,b):
    '''
    Returns a measurement object that is the subtraction of two measurements.
    '''
    a,b=check_values(a,b)
    #Propagating derivative of arguments    
    first_der={}
    a.check_der(b)
    b.check_der(a)
    for key in a.first_der:
        first_der[key]=a.first_der[key]-b.first_der[key] 
    if check_formula('-',a,b) is not None:
        return check_formula('-',a,b)
        
    #Addition by error propogation formula
    if measurement.method=="Derivative":
        mean=a.mean-b.mean
        std=error(a,b,der=first_der)
        result=function(mean,std)
    
    #Addition by Min-Max method
    elif measurement.method=="Min Max":
        result=add(a,-b)
        
    #Monte Carlo method
    else:
        minus=lambda x,y: x-y
        result=measurement.monte_carlo(minus,a,b)
    if a.info["Data"] is not None and b.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.subtract(a.info["Data"],b.info["Data"])
    result.first_der.update(first_der)
    result._update_info('-',a,b)
    return result

def mul(a,b):
    a,b=check_values(a,b)
    #Propagating derivative of arguments    
    first_der={}
    a.check_der(b)
    b.check_der(a)
    for key in a.first_der:
        first_der[key]=a.mean*b.first_der[key]+b.mean*a.first_der[key]
    if check_formula('*',a,b) is not None:
        return check_formula('*',a,b)
        
    #By error propogation formula    
    if measurement.method=="Derivative":          
        mean=a.mean*b.mean
        std=error(a,b,der=first_der)
        result=function(mean,std)
        
    #Addition by Min-Max method
    elif measurement.method=="Min Max":
        mean=a.mean*b.mean+a.std*b.std
        std=a.mean*b.std+b.mean*a.std
        result=function(mean,std)
            
    #If method specification is bad, MC method is used
    else:
        plus=lambda a,b: a*b
        result=measurement.monte_carlo(plus,a,b)
    if a.info["Data"] is not None and b.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.multiply(a.info["Data"],b.info["Data"])
    result.first_der.update(first_der)
    result._update_info('*',a,b)
    return result;
    
def div(a,b):
    a,b=check_values(a,b)
    #Propagating derivative of arguments    
    first_der={}
    a.check_der(b)
    b.check_der(a)
    for key in a.first_der:
        first_der[key]=(a.first_der[key]*b.mean-b.first_der[key]*a.mean)\
                / b.mean**2
    if check_formula('/',a,b) is not None:
        return check_formula('/',a,b)
        
    #By error propgation
    if measurement.method=="Derivative": 
        mean=a.mean/b.mean
        std=error(a,b,der=first_der)
        result=function(mean,std)
            
    #Addition by Min-Max method
    elif measurement.method=="Min Max":
        mean=(b.mean*a.std+a.mean*b.std)/(b.mean**2*b.std**2)
        std=(a.mean*b.mean+a.std*b.std+2*a.mean*b.std+2*b.mean*a.std)
        result=function(mean,std)
        
    #If method specification is bad, MC method is used
    else:
        divide=lambda a,b: a/b
        result=measurement.monte_carlo(divide,a,b)
    if a.info["Data"] is not None and b.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.divide(a.info["Data"],b.info["Data"])
    result.first_der.update(first_der)
    result._update_info('/',a,b)
    return result;

def power(a,b):
    #from math import log
    a,b=check_values(a,b)
    #Propagating derivative of arguments
    from math import log  
    first_der={}
    a.check_der(b)
    b.check_der(a)
    for key in a.first_der:
        first_der[key]=a.mean**b.mean*(b.first_der[key]*log(abs(a.mean))
                + b.mean/a.mean*a.first_der[key])  
    if check_formula('**',a,b) is not None:
        return check_formula('**',a,b)
    
    #By derivative method
    if measurement.method=="Derivative":
        mean=a.mean**b.mean
        std=error(a,b,der=first_der)
        result=function(mean,std)
        
    #By min-max method
    elif measurement.method=='Min Max':
        if (b<0):
            max_val=(a.mean+a.std)**(b.mean-b.std)
            min_val=(a.mean-a.std)**(b.mean+b.std)
        elif(b>=0):
            max_val=(a.mean+a.std)**(b.mean+b.std)
            min_val=(a.mean-a.std)**(b.mean-b.std)
        mid_val=(max_val+min_val)/2
        err=(max_val-min_val)/2
        result=function(mid_val,err)
    
    #By Monte Carlo method
    else:
        exponent=lambda a,b: a**b
        result=measurement.monte_carlo(exponent,a,b)
    if a.info["Data"] is not None and b.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.power(a.info["Data"],b.info["Data"])
    result.first_der.update(first_der)   
    result._update_info('**',a,b)
    return result;
        
        
def sin(x):
    from math import sin
    from math import cos
    
    x,=check_values(x)
    first_der={}
    for key in x.first_der:
        first_der[key]=cos(x.mean)*x.first_der[key]
    if check_formula('sin',x,func_flag=True) is not None:
        return check_formula('sin',x,func_flag=True)
        
    #By derivative method
    if measurement.method=='Derivative':
        mean=sin(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
        
    #By Monte Carlo method
    else:
        import numpy as np
        sine=lambda x: np.sin(x)
        result=measurement.monte_carlo(sine,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.sin(x.info["Data"])
    result.first_der.update(first_der)
    result._update_info('sin',x,func_flag=1)    
    return result;
    
def cos(x):
    from math import sin
    from math import cos

    x,=check_values(x)
    first_der={}
    for key in x.first_der:
        first_der[key]=-sin(x.mean)*x.first_der[key]    
    if check_formula('cos',x,func_flag=True) is not None:
        return check_formula('cos',x,func_flag=True)
    
    #By derivative method
    if measurement.method=='Derivative':        
        mean=cos(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
    
    #By Monte Carlo method
    else:
        import numpy as np
        cosine=lambda x: np.cos(x)
        result=measurement.monte_carlo(cosine,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.cos(x.info["Data"])
    result.first_der.update(first_der)
    result._update_info('cos',x,func_flag=1)
    return result;

def tan(x):
    from math import tan, sec
    
    x,=check_values(x)
    first_der={}
    for key in x.first_der:
        first_der[key]=sec(x.mean)**2*x.first_der[key]
    if check_formula('tan',x,func_flag=True) is not None:
        return check_formula('tan',x,func_flag=True)
    
    #Derivative method
    elif measurement.method=='Derivative':  
        mean=tan(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
    
    #Min-Max method
    elif measurement.method=='MinMax':  
        pass

    #Monte Carlo method
    elif measurement.method=='Monte Carlo':  
        import numpy as np
        tangent=lambda x: np.tan(x)
        result=measurement.monte_carlo(tangent,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.tan(x.info["Data"]) 
    result.first_der.update(first_der)
    result._update_info('tan',x,func_flag=1)
    return result;
    
def sec(x):
    from math import sec, tan
    
    x,=check_values(x)
    first_der={}
    for key in x.first_der:
        first_der[key]=sec(x.mean)*tan(x.mean)*x.first_der[key]
    if check_formula('sec',x,func_flag=True) is not None:
        return check_formula('sec',x,func_flag=True)
    
    #Derivative method
    elif measurement.method=='Derivative':  
        mean=sec(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
    
    #Min-Max method
    elif measurement.method=='MinMax':  
        pass

    #Monte Carlo method
    elif measurement.method=='Monte Carlo':  
        import numpy as np
        secant=lambda x: np.sec(x)
        result=measurement.monte_carlo(secant,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.sec(x.info["Data"]) 
    result.first_der.update(first_der)
    result._update_info('sec',x,func_flag=1)
    return result;

def csc(x):
    from math import csc, cot
    
    x,=check_values(x)
    first_der={}
    for key in x.first_der:
        first_der[key]=-cot(x.mean)*csc(x.mean)*x.first_der[key]
    if check_formula('csc',x,func_flag=True) is not None:
        return check_formula('csc',x,func_flag=True)
    
    #Derivative method
    elif measurement.method=='Derivative':  
        mean=csc(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
    
    #Min-Max method
    elif measurement.method=='MinMax':  
        pass

    #Monte Carlo method
    elif measurement.method=='Monte Carlo':  
        import numpy as np
        cosecant=lambda x: np.csc(x)
        result=measurement.monte_carlo(cosecant,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.csc(x.info["Data"]) 
    result.first_der.update(first_der)
    result._update_info('csc',x,func_flag=1)
    return result;

def cot(x):
    from math import csc, cot
    
    x,=check_values(x)
    first_der={}
    for key in x.first_der:
        first_der[key]=-csc(x.mean)**2*x.first_der[key]
    if check_formula('cot',x,func_flag=True) is not None:
        return check_formula('cot',x,func_flag=True)
    
    #Derivative method
    elif measurement.method=='Derivative':  
        mean=cot(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
    
    #Min-Max method
    elif measurement.method=='MinMax':  
        pass

    #Monte Carlo method
    elif measurement.method=='Monte Carlo':  
        import numpy as np
        cotan=lambda x: np.cot(x)
        result=measurement.monte_carlo(cotan,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.cot(x.info["Data"]) 
    result.first_der.update(first_der)
    result._update_info('cot',x,func_flag=1)
    return result;
    
def exp(x):
    from math import exp

    x,=check_values(x)
    first_der={}
    for key in x.first_der:
        first_der[key]=exp(x.mean)*x.first_der[key]     
    if check_formula('exp',x,func_flag=True) is not None:
        return check_formula('exp',x,func_flag=True)
    
    #By derivative method
    if measurement.method=='Derivative':
        mean=exp(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
    
    #By min-max method
    elif measurement.method=='Min Max':
        min_val=exp(x.mean-x.std)
        max_val=exp(x.mean+x.std)
        mid_val=(max_val+min_val)/x
        err=(max_val-min_val)/2
        result=function(mid_val,err)
        
    #By Monte Carlo method
    else:
        import numpy as np
        euler=lambda x: np.exp(x)
        result=measurement.monte_carlo(euler,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.exp(x.info["Data"]) 
    result.first_der.update(first_der)
    result._update_info('exp',x,func_flag=1)
    return result;

def e(value):
    measurement.exp(value)
    
def log(x):
    from math import log

    x,=check_values(x) 
    first_der={}
    for key in x.first_der:
        first_der[key]=1/x.mean*x.first_der[key]         
    if check_formula('log',x,func_flag=True) is not None:
        return check_formula('log',x,func_flag=True)
        
    #By derivative method
    if measurement.method=='Derivative':
        mean=log(x.mean)
        std=error(x,der=first_der)
        result=function(mean,std)
    
    #By Monte Carlo method
    else:
        import numpy as np
        nat_log=lambda x: np.log(x)
        result=measurement.monte_carlo(nat_log,x)
    if x.info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.log(x.info["Data"])
    result.first_der.update(first_der)
    result._update_info('log',x,func_flag=1)    
    return result;
  

def operation_wrap(operation,*args,func_flag=False):
    #if func_flag is not False:
    #    from math import sin,cos,tan,exp,log,cot,csc,sec
    args=check_values(args)
    if args[1] is not None:
        args[0].check_der(args[1])
        args[1].check_der(args[0])
    df={}
    for key in args[0].first_der:
        df[key]=diff[operation]*measurement.register[key].first_der
    if check_formula(op_string[operation],args,func_flag) is not None:
        return check_formula(op_string[operation],args,func_flag)   

    #Derivative Method
    if measurement.method=="Derivative":
        mean=operation(args)
        std=error(args,der=df)
        result=measurement(mean,std)
        
    #Min Max Method
        
    #Monte Carlo Method
    else:
        result=measurement.monte_carlo(operation,args)
    if args[0].info["Data"] is not None:
        import numpy
        result.info["Data"]=numpy.operation(args[0].info["Data"])   
    result.first_der.update(df)
    result._update_info(op_string[operation],*args,func_flag)

diff={sin:lambda x,key: cos(x.mean)*x.first_der[key],         
    cos:lambda x,key: -sin(x.mean)*x.first_der[key],
    tan:lambda x,key: sec(x.mean)**2*x.first_der[key],        
    sec:lambda x,key: tan(x)*sec(x)*x.first_der[key],
    csc:lambda x,key: -cot(x)*csc(x)*x.first_der[key],   
    cot:lambda x,key: -csc(x)**2*x.first_der[key], 
    exp:lambda x,key: exp(x)*x.first_der[key],           
    log:lambda x,key: 1/x*x.first_der[key],
    add:lambda a,b,key: a.first_der[key]+b.first_der[key],
    sub:lambda a,b,key: a.first_der[key]-b.first_der[key],
    mul:lambda a,b,key: a.first_der[key]*b.mean + b.first_der[key]*a.mean,
    div:lambda a,b,key: (a.first_der[key]*b.mean-b.first_der[key]*a.mean) \
                                                                / b.mean**2,
    power:lambda a,b,key: a.mean**b.mean*(b.first_der[key]*log(abs(a.mean))
                                            + b.mean/a.mean*a.first_der[key],)

}
      
op_string={sin:'sin',cos:'cos',tan:'tan',csc:'csc',sec:'sec',cot:'cot',
           exp:'exp',log:'log',add:'+',sub:'-',mul:'*',div:'/',power:'**',}