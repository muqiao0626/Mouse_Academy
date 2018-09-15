import sys, os
import execnet

def call_python_version(Version, Module, Function, ArgumentList):
    gw      = execnet.makegateway("popen//python=python%s" % Version)
    channel = gw.remote_exec("""
        from %s import %s as the_function
        channel.send(the_function(*channel.receive()))
    """ % (Module, Function))
    channel.send(ArgumentList)
    return channel.receive()

def main():
    result = call_python_version("2.7", "TestDisplayPy2", "mainTest",  
                             [])
    print('result:', result)
    
if __name__ == "__main__":
    main()