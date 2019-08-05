import linecache
import sys
import time
import asyncio

def log_exc(func):
    def new_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, f.f_globals)
            msg = 'EXCEPTION ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)
            print("Decorator error! ", msg)
            return msg
    return new_func


class log_cls_methods(type):
    def __new__(cls, name, bases, local):
        for attr in local:
            value = local[attr]
            if callable(value):
                local[attr] = log_exc(value)
        return type.__new__(cls, name, bases, local)

def measure_latency(f):
    def new_f(*args, **kwargs):
        t1 = time.time()
        result = f(*args, **kwargs)
        t2 = time.time()
        result['latency'] = t2 - t1
        return result
    return new_f

def async_measure_latency(f):
    async def new_f(*args, **kwargs):
        t1 = time.time()
        result = f(*args, **kwargs)
        t2 = time.time()
        result['latency'] = t2 - t1
        return result
    return new_f


def rate_limiter(obj, delay):
    def decorator(function):
        def wrapper(*args, **kwargs):
            f_name = function.__name__+str(id(function))
            if hasattr(obj, f_name):
                rate_data = getattr(obj, f_name)
                last = rate_data['last']
                current = time.time()*1000
                if current < last + delay:
                    time.sleep((last + delay - current)/1000)
                    current = time.time() * 1000
                res = function(*args, **kwargs)
                setattr(obj, f_name, {'last':current})
            else:
                res = function(*args, **kwargs)
                current = time.time() * 1000
                setattr(obj, f_name, {'last': current})
            return res

        return wrapper
    return decorator

def async_rate_limiter(obj, delay):
    def decorator(function):
        async def wrapper(*args, **kwargs):
            f_name = function.__name__+str(id(function))
            if hasattr(obj, f_name):
                rate_data = getattr(obj, f_name)
                last = rate_data['last']
                current = time.time()*1000
                if current < last + delay:
                    asyncio.sleep((last + delay - current)/1000)
                    current = time.time() * 1000
                res = function(*args, **kwargs)
                setattr(obj, f_name, {'last':current})
            else:
                current = time.time() * 1000
                res = function(*args, **kwargs)
                setattr(obj, f_name, {'last': current})
            return res

        return wrapper
    return decorator


