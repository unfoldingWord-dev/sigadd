SigAdd
---

This script allows Signing Entities to submit content signatures for inclusion in the api

###Requirements

####OpenSSL
This tool requires the `SHA384` hash algorithm which is available in OpenSSL 1.0.1.e and newer.
If your version of OpenSSL does not support the correct hash algorithm you will likely receive an error message as shown below
```
$ Error Verifying Data
$ 10308:error:0606C06E:digital envelope routines:EVP_VerifyFinal:wrong public key type:.\crypto\evp\p_verify.c:85:
```
When debugging this tool always make sure you have the correct version of OpenSSL first.

###Example

First start up the script with your desired port
```
$ python index.py 88
```

The service will now be listening at `127.0.0.1:88`

Given the following data below:
```
{
  "content": "https://api.unfoldingword.org/obs/txt/1/en/obs-en.json?date_modified=20150210",
  "sig": "MGYCMQDN7R4lTqR579DwbEQjGa7gBDlQrqv84fv7EPJoTC7XwYK0H2ODQ3UQL5QaOiE2+h0CMQC0JPChVkm8FbX+OhFNFl8D1bp96dMpdE6XOchCE0j/tDACWIQGV/icjbD4m5yb2Vk=",
  "slug": "uW"
}
```

Perform a post request to wherever the script is listening (127.0.0.1:88 in this example):
```
$ curl -X POST --data-urlencode "data=<data above with quotes escaped and no newlines>" http://127.0.0.1:88
```

e.g.

```
$ curl -X POST --data-urlencode "data={\"content\":\"https://api.unfoldingword.org/obs/txt/1/en/obs-en.json?date_modified=20150210\",\"sig\":\"MGYCMQDN7R4lTqR579DwbEQjGa7gBDlQrqv84fv7EPJoTC7XwYK0H2ODQ3UQL5QaOiE2+h0CMQC0JPChVkm8FbX+OhFNFl8D1bp96dMpdE6XOchCE0j/tDACWIQGV/icjbD4m5yb2Vk=\",\"slug\":\"uW\"}" http://127.0.0.1:88
```

> Note: in production this script will be located at https://api.unfoldingword.org/sigadd/