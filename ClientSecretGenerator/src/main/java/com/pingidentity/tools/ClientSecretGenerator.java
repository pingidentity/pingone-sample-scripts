package com.pingidentity.tools;

import com.turo.pushy.apns.auth.ApnsSigningKey;
import org.jose4j.json.internal.json_simple.JSONObject;
import org.jose4j.jws.AlgorithmIdentifiers;
import org.jose4j.jws.JsonWebSignature;

import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.security.PrivateKey;
import java.util.Date;

public class ClientSecretGenerator {

    public static void main(String[] args) {
        ClientSecretGenerator csg = new ClientSecretGenerator();
        System.out.println(csg.createSecret(args));
    }

    /**
     * Create a JWT used as client_secret
     *
     * @args [0]: kid, [1]: iss, [2]: exp, [3]: sub, [4]: path-to-key
     * return null if something went wrong, a JSON document otherwise
     */
    String createSecret(String[] args) {

        if (args.length != 5) {
            System.err.println("Usage: java -jar ClientSecretGenerator.jar kid iss exp sub path-to-private-key");
            System.err.println("kid: the key ID to use, given by Apple and associated with the private key");
            System.err.println("iss: the Team_ID as found in the Apple developer account");
            System.err.println("exp: the number of days for which the secret should be valid for (1-60)");
            System.err.println("sub: the client_id");
            System.err.println("path-to-private-key: absolute path to the private key issued by Apple (i.e.: AppleKey.p8)");
            return null;
        }

        int iat = Integer.parseInt(String.valueOf(new Date().getTime()).substring(0, 10));
        int exp = 0;
        try {
            exp = Integer.parseInt(args[2]);
            if(exp < 1 || exp > 60) {
                throw new IllegalArgumentException();
            }
            exp = iat + (exp * 86400);
        } catch (Exception e) {
            System.err.println("The exp value could not be parsed to an integer value or it is not between 1-60 (days)");
            return null;
        }

        JSONObject payload = new JSONObject();
        payload.put("iss", args[1]);
        payload.put("exp", exp);
        payload.put("sub", args[3]);
        payload.put("iat", iat);
        payload.put("aud", "https://appleid.apple.com");

        try {
            String clientSecret = generateJwt(args[0], args[4], payload);
            JSONObject output = new JSONObject();
            output.put("payload", payload);
            output.put("client_secret", clientSecret);
            return output.toJSONString();
        } catch (Exception e) {
            System.err.println("The client_secret could not be generated: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    private String generateJwt(String kid, String pathToKey, JSONObject payload) throws Exception {
        JsonWebSignature jws = new JsonWebSignature();
        jws.setPayload(payload.toJSONString());
        jws.setAlgorithmHeaderValue(AlgorithmIdentifiers.ECDSA_USING_P256_CURVE_AND_SHA256);
        jws.setKeyIdHeaderValue(kid);
        PrivateKey privateKey = getPrivateKey(pathToKey);
        jws.setKey(privateKey);
        return jws.getCompactSerialization();
    }

    private PrivateKey getPrivateKey(String filename) throws Exception {
        File f = new File(filename);
        FileInputStream fis = new FileInputStream(f);
        DataInputStream dis = new DataInputStream(fis);
        byte[] keyBytes = new byte[(int) f.length()];
        dis.readFully(keyBytes);
        dis.close();
        return ApnsSigningKey.loadFromPkcs8File(new File(filename), "Team_ID", "KeyID");
    }
}