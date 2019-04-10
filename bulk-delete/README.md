# Bulk Delete

This is a sample script detailing a bulk deletion of users in an environment.

## Required Parameters

* `ENVIRONMENT_ID`: The ID of the environment in which the users you wish to delete are stored. It should also be the same environment as the client app.
* `CLIENT_ID`: The ID of an app configured with the ability to delete users (see [App Configuration](#app-configuration)). The ID of your app can be found in the Applications section under the Connection tab in the admin console. 
* `CLIENT_SECRET`: The corresponding secret of an app configured with the ability to delete users (see [App Configuration](#app-configuration)). To find your app's secret, navigate to your app in the Applications section under the Connection tab in the admin console. The client secret can be found under the Configuration tab of your app.

## Optional Parameters

* `POPULATION_ID`: The ID of the population in which the users you wish to delete are stored.
* `QUERY`: A SCIM 2.0 filter can be used to match the user resources to return. If this parameter is omitted, all users in the given environment will be deleted. Only a subset of the standard SCIM 2.0 filter operators are supported: `eq`, `sw`, `and`, and `or`.
* `SKIP_USER_IDS`: An array of user IDs as strings may be provided to exclude specific users from the deletion. If this parameter is omitted, all users in the environment matching the given query will be deleted.

## App Configuration

For this operation, you will need an app configured with
* `Token` response type
* `Client Credentials` grant type
* `Client Secret Basic` authentication method
as well as the `p1:read:env:user` and `p1:delete:env:user` scopes.

To create or modify an existing application, navigate to the Applications section under the Connection tab in the admin console.

## Example Usage

Delete all users in a population, skipping two users:
```
./bulk-delete.py -e env-id-123 -c client-id-123 -s client.secret~!! -p population-id-123 -w user-id-123 user-id-456
```

Delete all disabled users in a population:
```
./bulk-delete.py -e env-id-123 -c client-id-123 -s client.secret~!! -p population-id-123 -q 'enabled eq false'
```