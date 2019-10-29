package com.pingidentity.tools;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.util.Date;
import org.jose4j.json.internal.json_simple.JSONObject;
import org.jose4j.json.internal.json_simple.parser.JSONParser;
import org.jose4j.jws.JsonWebSignature;
import org.jose4j.jwx.JsonWebStructure;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

public class TestClientSecretGenerator {

    private final ByteArrayOutputStream outContent = new ByteArrayOutputStream();
    private final ByteArrayOutputStream errContent = new ByteArrayOutputStream();
    private final PrintStream originalOut = System.out;
    private final PrintStream originalErr = System.err;

    private ClientSecretGenerator csr;
    private String iss, sub, kid, path;
    private int exp;

    @Before
    public void setup() {

        System.setOut(new PrintStream(outContent));
        System.setErr(new PrintStream(errContent));

        // args [0]: kid, [1]: iss, [2]: exp, [3]: sub, [4]: path-to-key
        kid = "mykid";
        iss = "myissuer";
        exp = Integer.parseInt(String.valueOf((new Date().getTime() / 1000) + 3600));
        sub = "mysub";
        path = "src/test/resources/example.p8";
        csr = new ClientSecretGenerator();
    }

    @After
    public void tearDown() {
        System.setOut(originalOut);
        System.setErr(originalErr);
    }

    @Test
    public void testMissingArgs() {
        String[] args = new String[0];
        assertNull(csr.createSecret(args));
        assertTrue(errContent.toString().contains("path-to-private-key: absolute path to the private key issued by Apple (i.e.: AppleKey.p8)"));
    }

    @Test
    public void testExpNoDigits() {
        String[] args = new String[]{kid, iss, "ab", sub, path};
        csr.createSecret(args);
        assertEquals("The exp value could not be parsed to an integer value or it is not between 1-60 (days)\n", errContent.toString());
    }

    @Test
    public void testExpTooLarge() {
        String[] args = new String[]{kid, iss, "61", sub, path};
        csr.createSecret(args);
        assertEquals("The exp value could not be parsed to an integer value or it is not between 1-60 (days)\n", errContent.toString());
    }

    @Test
    public void completeExample() {
        String[] args = new String[]{kid, iss, "10", sub, path};
        try {

            JSONObject output = (JSONObject) new JSONParser().parse(csr.createSecret(args));
            String jwt = (String)output.get("client_secret");
            JsonWebStructure jws =  JsonWebSignature.fromCompactSerialization(jwt);
            assertEquals("ES256", jws.getAlgorithm().getAlgorithmIdentifier());
            assertEquals(kid, jws.getKeyIdHeaderValue());

            JSONObject pl = (JSONObject)new JSONParser().parse(((JsonWebSignature) jws).getUnverifiedPayload());
            assertEquals(iss, pl.get("iss"));
            assertEquals(sub, pl.get("sub"));
            long now = new Date().getTime();
            long genExp = now + (10*86400*1000);
            assertEquals(String.valueOf(genExp).substring(0,8), String.valueOf(pl.get("exp")).substring(0, 8)); // testing if the exp date is at least in the range of where it should be

        } catch (Exception e) {
            e.printStackTrace();
            fail();
        }
    }
}