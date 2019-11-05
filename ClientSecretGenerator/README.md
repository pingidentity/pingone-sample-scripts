# Ping Identity - SiwaClientSecretGenerator

To leverage *Sign In with Apple* a developer has to generate the client_secret based on a private key, expressed as JWT.
To make this easier we have developed a simple tool that helps doing that.

The tool can be used as follows:

```java -jar SiwaClientSecretGenerator.jar {kid} {iss} {exp} {sub} {/path/to/key.p8}```

- **{kid}:** The associated keyID which will be used as **kid** in the JWT header
- **{iss}**: The Team_ID as found in the Apple developer account
- **{exp}**: The number of days for which the secret should be valid for (1-60)
- **{sub}**: The client_id of the service using this client_secret
- **{/path/to/key.p8}**: Absolute path to the private key that was created in Apple developer console 

The tool can be found in the **./dist** directory.

## Building the tool

To build the tool Make and Maven are required. Clone this project and run this command:

- ```$ make build_all```
- ```cd ./dist```
- ```java -jar SiwaClientSecretGenerator.jar ...```

The generated JSON output includes the client_secret (JWT) and the payload for your convenience. It will look like this:

    {
        "client_secret": "the-generated-jwt",
        "payload": {
            "sub": "your-client-id",
            "aud": "https://appleid.apple.com",
            "iss": "your-issuer",
            "exp": 1572304753,
            "iat": 1572303895
        }
    }
    
We hope this helps you to get ahead with your development faster!