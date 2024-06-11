import http from "k6/http";
import {check, sleep} from "k6"


export function hit() { 
    let url = "http://spamoverflow-1073304328.us-east-1.elb.amazonaws.com/api/v1/" + "customers/63aa69ad-4e47-4bc5-97ed-9e0bd6255278/emails"; 
  
    const payload = JSON.stringify({
        "contents": {
            "to": "efake@2k.com",
            "from": "c@c",
            "subject": "objective",
            "body": "6.com, 57.com"
            },
        
        "metadata": {
            "spamhammer": "0|12"
            }
    }); 
  
    const params = { 
       headers: { 
          'Accept': 'application/json', 
       }, 
    }; 
  
    let request = http.post(url, payload, params); 
    check(request, { 
       'is status 201': (r) => r.status === 201, 
    }); 
  
    sleep(10); 
  
    request = http.get(url); 
    check(request, { 
       'is status 200': (r) => r.status === 200,
    }); 
  
    sleep(10); 
}


export const options = { 
    scenarios: { 
       hits: { 
          exec: 'hit', 
          executor: "ramping-vus", 
          stages: [ 
             { duration: "2m", target: 10000 }
          ], 
       }
    }, 
 };