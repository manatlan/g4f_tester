#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import g4f,asyncio,os
from datetime import datetime


#################################################################
from g4f.client import AsyncClient
import g4f.providers
import g4f.providers.retry_provider


async def ask(content:str,model:str,timeout=60) -> str:
    try:
        messages = [dict(role="user",content=content)]
        client = AsyncClient()
        coro = client.chat.completions.create(model=model,messages=messages)  # type: ignore
        response = await asyncio.wait_for(coro,timeout=timeout) # type: ignore
        return response.choices[0].message.content
        # coro = g4f.ChatCompletion.create_async(model=model, messages=messages) # type: ignore
        # response = await asyncio.wait_for(coro,timeout=timeout) # type: ignore
        # return response        

    except Exception as e:
        return "ERROR: "+str(e)
#################################################################

def get_models() -> list[tuple[str,str,list]]:
    """ retourne [(model,society,providers)] classe par celui qui a le plus de providers """
    all=[]
    for model in g4f.models._all_models:
        m=g4f.models.ModelUtils.convert[model]
        o=m.best_provider
        if o is None:
            providers=[]
        elif isinstance(o,g4f.providers.retry_provider.IterListProvider):
            providers=o.providers
        else:
            providers=[o]
        all.append( (m.name, m.base_provider, providers) )

    all.sort(key=lambda x: -len(x[2]))
    return all


# from g4f.cookies import set_cookies_dir, read_cookie_files

import g4f.debug
g4f.debug.logging = True

# cookies_dir = os.path.join(os.path.dirname(__file__), "har_and_cookies")
# set_cookies_dir(cookies_dir)
# read_cookie_files(cookies_dir)

import json
class DB:
    def __init__(self):
        if os.path.isfile("db.json"):
            self.db=json.load( open("db.json") )
        else:
            self.db=[]
    def maj(self, g4f:str, model:str, nb:int, ok:bool ,txt:str):
        found=False
        for idx,(g,m,n,o,t) in enumerate(self.db):
            if g==g4f and m==model:
                found=True
                self.db[idx] = (g4f,model,nb,ok,txt)
        if not found:
            self.db.append( (g4f,model,nb,ok,txt) )
        
    def get_models(self):
        return sorted(list({m for (g,m,n,o,t) in self.db}),key=lambda x: x.lower())

    def get_g4fs(self):
        return sorted(list({g for (g,m,n,o,t) in self.db}))

    def get(self, g4f:str, model:str):
        for (g,m,n,o,t) in self.db:
            if g==g4f and m==model:
                return (n,o,t)


    def save(self):
        with open("db.json","w+") as fid:
            fid.write( json.dumps(self.db,indent=4) )

if __name__ == "__main__":
    v=g4f.version.utils.current_version 

    async def test(db,content,model,nb_providers:int):
        print("test",model,nb_providers,"...")
        t=datetime.now()
        x:str= await ask(content,model)
        t=datetime.now() -t
        ok = False if x.startswith("ERROR:") else True
        db.maj(v,model,nb_providers,ok,x)
        print(model,"=>",ok)

    async def megatest(content):
        db=DB()
        tasks=[]
        for model,society,providers in get_models():
            tasks.append( asyncio.create_task( test(db,content, model,len(providers)) ) )
        await asyncio.gather(*tasks,return_exceptions=True)    
        db.save()

    asyncio.run(megatest("Combien font 2 x 21"))

    db=DB()
    with open("results.md","w+") as fid:
        vs=db.get_g4fs()
        ll=["models"]+vs
        fid.write(f"|{'|'.join(ll)}|\n")
        fid.write(f"|{'|'.join(['---' for i in ll])}|\n")

        for model in db.get_models():
            vv=[]
            for v in vs:
                nott=db.get(v,model)
                good=""
                if nott:
                    n,o,t = nott
                    if o: 
                        #good=f"{v}({n})"
                        good="🟢%s(%s)" % (model,n)
                    else:
                        good="🔴%s" % model
                vv.append( f"{good:13s}" )
            fid.write(f"|{model:20s}|{'|'.join(vv)}|\n")

