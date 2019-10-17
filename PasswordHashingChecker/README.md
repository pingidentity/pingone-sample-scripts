This Java (1.8) tool helps to check that your algorithm matches the algorithm that PingOne for Customers uses to read encoded
passwords. You can compare your algorithm's output with the one you get from running this tool to see if they're
compatible. 

This tool takes a clear-text password**, a salt, and a hashing scheme (message digest); and it outputs the hashed 
password according to [Lightweight Directory Access Protocol (LDAP): Hashed Attribute values for 'userPassword'](https://tools.ietf.org/id/draft-stroeder-hashed-userpassword-values-01.html).

The message digest schemes it currently accepts are:
  * SSHA
  * SSHA256
  * SSHA384
  * SSHA512

*This tool is meant as a helpful check, but it should not be relied on solely.
**Passwords are in cleartext, so don't use real passwords unless you really know what you're
                  doing!
 
 ### How to Run
 1. Download this repository
 2. Navigate inside
 3. Run mvn install
 4. Run java -jar target/PingOneforCustomersPasswordChecker-1.0-SNAPSHOT.jar