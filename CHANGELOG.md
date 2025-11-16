## [1.1.0](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/compare/1.0.1...1.1.0) (2025-11-16)


### Features

* add artifact module (initial import) + test package cleanup ([e9ae330](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e9ae330683bb8c42a70d54ad1181098723563fc4))
* **api:** add health endpoint, categories APIs, and auth metadata (ip/user_agent) + logout ([33404fb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/33404fbda37db721ec5e8bf8ddfc7002ab377368))
* **api:** add logging for API calls and resource management in api.py ([e211eca](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e211eca6666876e860ec3b2f3ca06b0ea9e6b721))
* **api:** add optional category_id to api_add_expense while keeping full backward compatibility ([0b573fb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0b573fb7696e77df45fe2ee7ce06c5f4aeb7792b))
* **api:** add update endpoints and contact-balance API, make get_db thread-safe, and propagate ordering/pagination ([34b7969](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/34b796916b57fe0785a6287d1f03531b9a1d99cb))
* **api:** add user registration and authentication endpoints to unified API ([001511b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/001511bedc348d69075c198978cc85af95d4c264))
* **api:** expose api_get_user_net_balance and api_get_user_balance_breakdown ([93a1c5c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/93a1c5c2d99cb4a4bbabf51d8628532e65f81d85))
* **api:** expose new endpoints and standardize envelopes/logging across data layer ([d979f8c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d979f8c1696256e874158e99f4a502dac79d64e7))
* **api:** forward role to registration and is_admin to transactions in MoneyMate/data_layer/api.py ([df1f5fc](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/df1f5fc4f1c8f0ffe2f1a01ae899e8fb8e75a6f2))
* **api:** make API database configurable for tests and future extensions ([2199e21](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/2199e2102c5c4c2316851a1031ecc351f135dab1))
* **api:** support user-scoped expense, contact, transaction operations and user-to-user credits/debits ([c537a2a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/c537a2a579937e490cfcacdc21281c4c82fbece5))
* **api:** unified high-level API with user-scoped operations; pagination/sorting; admin views; health and list_tables endpoints ([e200025](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e2000259243e5b206d3de170482527417215d7b9))
* **categories:** add ordering/pagination, trim name, and idempotent delete; return friendly error on duplicates ([bf637ad](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/bf637ad363d67fec7bf5f4b4064f3d60c86012a6))
* **categories:** implement CategoriesManager CRUD (add/get/delete) with per-user checks and logging ([cde7fff](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cde7fffc8158a1586577b4503787a0f24839506e))
* **categories:** per-user categories CRUD with per-user UNIQUE constraint and optional pagination ([0d520fd](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0d520fdc4017121e3159ae73cd28bf4e1238e6de))
* **contacts:** add logging for CRUD operations and errors in ContactsManager ([4a94288](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/4a94288b64135cb28c1c19248afc2f24bb9a1e38))
* **contacts:** associate contacts to users and add user-scoped CRUD operations ([2065613](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/2065613f8ca1f2c8afd82ef422a8f672c1ea2088))
* **contacts:** per-user contacts CRUD with validation and deterministic ordering ([22fa9f8](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/22fa9f8849be98d96f8622f4c3f7f61e006d8c46))
* **contacts:** trim input, support ordering, and make delete idempotent with clear logging; map UNIQUE to friendly error ([7097363](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/70973637644ff27f1dd74b2184764766222c4afc))
* **data_layer/manager.py:** add close() and reset_db() methods for DB resource management ([32f896d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/32f896d16e7f08e0f25881bba4f22d7acb81470e))
* **data_layer:** implement user registration and authentication logic in UserManager ([56820c8](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/56820c807754ffe4e22db17e2baa50c0e3af7192))
* **data-layer:** add contact balance calculation ([90c8c1c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/90c8c1c9ccf3d18ebcb5ada5d4ebed2acee0f95c))
* **data-layer:** add DatabaseManager class and database initialization ([a1dc3f6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a1dc3f610821f35e8f5c4f8f1a6a3a9ff411e46a))
* **data-layer:** add validation functions for expenses, contacts, and transactions ([59356f1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/59356f1a7b79e3a0f3c45fa47ed6a8740cef60e5))
* **data-layer:** implement CRUD for contacts (add, get, delete) ([418ef4a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/418ef4aa940afbe82c366420e2605006f6ab9076))
* **data-layer:** implement CRUD for transactions ([5d7ea82](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5d7ea82d640e0e0f05e866fd1a3dcb2d9f94fb77))
* **data-layer:** implement CRUD operations for expenses (add, get, search, delete, clear) ([5d85b4e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5d85b4e42d6f2d6f46b7b8ab94da238d9c46884c))
* **data-layer:** return dicts instead of tuples, add table listing, improve validation and error messages ([093d316](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/093d316dec221d41071fe382e3216b6bb89de69f))
* **database:** add categories/notes/attachments/access_logs tables, expenses.category_id, and stronger FKs/indexes ([f488dcd](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f488dcdb8f564c2d344a8d8a1f42204a08ec7c9d))
* **database:** add logging for connection, initialization, and table listing in database.py ([bedc394](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/bedc3947321563200dcf3a093ebece60e483dd0e))
* **database:** add per-user tracking to expenses, contacts, and user-to-user transactions table ([e299467](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e299467adf9c9d0e60938498a8808cc46aa3b288))
* **database:** add role field to users table for role-based access control and admin logic in database.py ([89c7695](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/89c7695feb46e795d93d359d5a79f2abdcc04dbd))
* **database:** add schema versioning scaffold and enforce CHECK constraints for new DBs ([592ec0d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/592ec0d89e6f5d0b7eda3f5c4e8963b09030e79b))
* **database:** add users table to database schema for user management ([a45c331](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a45c3316db6bd419854f46d03e7189169989dcb1))
* **database:** initialize SQLite schema (users, contacts, expenses with optional category_id, transactions, categories, notes, attachments, access_logs); enable FKs and indexes ([531cb17](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/531cb17990c2faf8e22bbda0ee77f41e80bd1aa4))
* **database:** support SQLite URI for shared in-memory DB; add schema_version table and get_schema_version; add composite indexes; ensure expenses.category_id index ([f239595](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f2395959b7f0dc89cec14ee78c76fa20706c3d4b))
* **data:** creating data_layer.py for database and CRUD scaffolding ([9c88385](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9c88385d8012be0c76e36599d4d7a3a1676fe83b))
* **db:** add SQL auth schema and init script; ignore local *.db ([50a26a4](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/50a26a482cf6b95658fb5802631d9391e7fbde7a))
* **expenses:** associate expenses to users and add user-scoped CRUD operations ([042d997](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/042d997a69b0316137546c03f451ba977d1df362))
* **expenses:** implement partial updates, search with ordering/pagination, idempotent delete, and optional category_id ([d71515a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d71515a78d0836dd0c3878698abdae8c3bdc021f))
* **expenses:** integrate logging in ExpensesManager for validation, operations and error handling ([81d969e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/81d969e3ab47d515b8218684ea7dab1bd0d67a9a))
* **expenses:** per-user expenses CRUD; optional category_id with ownership validation; list/search with ordering, date range, and pagination ([aa47a0b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/aa47a0b7064a11c0886856083d58c91de7cbf8ec))
* **expenses:** support category_id with schema detection and per-user validation; include it in queries ([502f0f6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/502f0f6b5c9518c697ba13b6bfadc6c9ffe6948c))
* **gui/categories:** add CRUD UI with refresh and robust validation/messages ([0378df5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0378df5d753daadc75e3ff616af15cdd27baf5ae))
* **gui/charts:** implement dashboard charts with graceful matplotlib/Tk fallback ([9c4224d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9c4224d0f878ef8d9dac3ec9600f63cfeff3e20e))
* **gui/contacts:** implement search and CRUD flows with consistent messageboxes ([853f2fb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/853f2fb79c20e1cc19bf73256af5d4187a023bb8))
* **gui/expenses:** add batch insertion, search, update and clear with validation ([584f240](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/584f2405fe60f484de52cf5ae6f2b6b29b429ea5))
* **gui/login:** enhance login validation and integrate navigation to registration ([88e5743](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/88e57431d5a0a8e1cca1333940ece93d1dfb71e7))
* **gui/register:** add registration screen with validation and API hook ([41cc105](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/41cc105546f7962ad256f7ba809797c07345c26b))
* **gui/transactions:** add filters, contact mapping and balance display with refresh ([a1d589d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a1d589d7c01e13c5c52b76385f38c0afc2a74036))
* **gui:** integrate RegisterFrame and safe frame refresh with sidebar navigation ([7f54663](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7f546637655d14ab972caeda494848d0fa4c989d))
* **manager): add keeper connection for shared in-memory DB and wire CategoriesManager; manage keeper lifecycle in close/set_db_path feat(api:** add health endpoint, categories APIs, and auth metadata (ip/user_agent) + logout ([8823740](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8823740aea895dca86baa863bd7335ed507a035f))
* **manager:** add DatabaseManager class to centralize entity managers and maintain full logic ([3246874](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/324687493292a01d545be528d1fc266521a3bff8))
* **manager:** add logging for initialization, manager re-creation, cleanup and table listing in DatabaseManager ([b9ddcf9](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b9ddcf98131f296e011a76bdd4574f3d71776431))
* **manager:** add set_db_path method for dynamic database switching ([e941aba](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e941aba99a3cbaf7560c590f8bab32fd97035044))
* **manager:** ensure manager supports new user role logic and admin features in manager.py ([af55cd8](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/af55cd887b71678df5d3b230b57755883db1a151))
* **manager:** initialize and expose managers, support shared in-memory keeper, and add typed interfaces ([e6095b6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e6095b62711406e59c17f07b439be94a467ce27e))
* **test:** add user registration to fixtures and test logging for user-scoped entities and user-to-user transactions in test_logging.py ([9adc5b3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9adc5b33ab2c335fee3de70a6e837ef265979039))
* **test:** add user registration to fixtures and test logging for user-scoped entities and user-to-user transactions in test_logging.py ([0a06849](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0a06849e00283639d72f0104d1c1996c3d129a30))
* **test:** add user registration/login and unique username/authentication tests for usermanager in test_usermanager.py ([b6cee6d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b6cee6daf65832e95ca5a270750016414b45134c))
* **test:** expect users/expenses/contacts/transactions tables in schema for database tests ([f8f0b54](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f8f0b5473b884f963bb4f3166f8880ecab36bb7a))
* **test:** refactor test_transactions.py for user-to-user logic, user_id param, and proper CRUD checks ([0c1c4d1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0c1c4d1bbac292f0fbc1fae906e75c9f49cca5a6))
* **test:** refactor test_transactions.py for user-to-user logic, user_id param, and proper CRUD checks ([654debb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/654debbf3f2fb2c7250c89fb1a4b2af8b4cd6c19))
* **test:** update API tests for user-scoped operations and user-to-user transactions ([339b01a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/339b01a45ef617255329114e0940df6b9ce9fa13))
* **test:** update contact tests for per-user contact management ([51a455d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/51a455d47972de6ea5e8a09cf9506bf914fca861))
* **test:** update manager table listing test to expect users/contacts/expenses/transactions tables in test_manager.py ([f3cee19](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f3cee19f316adc653994b36d9525f014e5eafdb3))
* **test:** update test_api.py for user-scoped expense/contact/transaction operations and user-to-user transaction logic ([60b787e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/60b787e34e237948832b4f24b8e1bda349a6fa15))
* **test:** update test_expenses.py for per-user expense isolation, CRUD, and user_id param ([7f21b19](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7f21b19c77c25acd929636d69dffe5882c1c99a9))
* **transactions:** add existence check for sender/receiver user_id on transaction insert and improve transaction manager for user-centric logic ([9eda6d3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9eda6d36b51fadc94f932d3b9c88d56129e1fe4d))
* **transactions:** add get_user_net_balance and get_user_balance_breakdow; keep legacy get_user_balance for compatibility ([4af6c54](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/4af6c5427cb6c070687d244d9112b0c9f9e2c0f7))
* **transactions:** add logging for CRUD operations, validation and errors in TransactionsManager ([bf27ff5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/bf27ff51241c30d801ec50646d04fceb6db7be2e))
* **transactions:** add net/breakdown APIs and contact auto-resolve with admin checks ([22ac13d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/22ac13d7638845b1b661637a6cf548efcdb2c5e4))
* **transactions:** add support for user-to-user credits/debits and user-scoped transaction queries ([a6ef098](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a6ef098f7f486f8afbb6b1f386d7e9a536cf7cee))
* **transactions:** allow admin to view all transactions and support is_admin flag in get_transactions in transactions.py ([93e6ad9](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/93e6ad95bd6983df3e7130d0c4e32592cafadd3c))
* **transactions:** implement partial updates, admin visibility with validation, idempotent delete, and per-contact balance ([d664193](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d66419338f6aea34da54fbb7725a6f9593cebf14))
* **transactions:** redefine balance as credits received minus debits sent; update calculation and logs ([b23da56](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b23da56d6786f76bc6afaa256dad941cee650050))
* **transactions:** user-to-user transactions with validation, admin-wide listing, filters/pagination, sender-ownership delete, and balance calculations ([7c82506](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7c825065b935b0a379e0d155f5676fbe77b7f794))
* **user:** add user lookup/list users and stricter admin/role handling ([cb627f3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cb627f3831ee534b7c87e715a9f334de2f6af6f6))
* **usermanager:** accept ip_address/user_agent on login and add logout_user with audit logging ([5e97b4d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5e97b4dcef895c4683b2ac7a8443de433f462494))
* **usermanager:** enforce admin password '12345' and add role logic to user registration and management in usermanager.py ([86fc8ef](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/86fc8ef7752c2e804192c5a8242364fc7ef0154e))
* **usermanager:** log login/failed_login/password_change/password_reset to access_logs with graceful fallback ([1ba44eb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/1ba44eba8e8778a11af59d89b72da452cb662f19))
* **users:** enforce admin registration policy, add access logs, password change/reset, roles, and input normalization ([3b06480](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/3b06480f64800dbb184b0db5c85c1b6cb98ed573))


### Dependency updates

* **deps:** add Werkzeug to requirements.txt for secure password hashing in user management ([852f580](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/852f580f1c60d4c402732b7342ac260262f0ebdf))


### Bug Fixes

* **api.py:** calling set_db_path(None) now safely releases the global DB without opening a connection ([7e0a32c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7e0a32c091f350ecba0865331612b43f4e981852))
* **ci:** correct malformed include line in requirements-dev.txt ([cda8ce5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cda8ce53afb6f7ed247d935ce4da8b714fc99ce8))
* **data_layer:** add _create_managers method in manager.py ([86a432b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/86a432ba60b4c9f29b16c22f2b3908d11a907809))
* **data_layer:** removed external data_layer folder, uselessand could create problems ([a35459d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a35459dc62bc639d99f2fc69ee019a2b7662da9e))
* **database:** restore DB_PATH and switch users to password_hash; keep schema extensions (categories, notes, attachments, access_logs) and expenses.category_id ([589dcd9](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/589dcd9bb9de26d775940489acd1a7d9e2be02a9))
* **expenses:** correct validation implementation in validation.py ([bb0cfad](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/bb0cfadc7fc5878e8b9caed71d57447873b0787f))
* **gui:** Resolve TclError by using grid in LoginFrame ([08dc5ed](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/08dc5eddc0ef339cf6dc455b75faadcce1e7a140))
* manager.py update and small changes to pass tests ([3dcfd44](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/3dcfd445789b6bb6d3e6ff839f8d596bc6eb5ef8))
* remove stray init.py and keep only __init__.py to resolve import issues ([2e55302](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/2e5530271a7908e380de3f521e9a1acf1955c2f6))
* small changes (wrapper) to guarantee tests ([24de501](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/24de501ba6c96e700c9dc2d7f857b53a44974090))
* **test_tables_exist:** ignore sqlite_sequence system table when checking DB structure ([a6900d0](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a6900d0eb67e0ba4c9ac21329c4dc2204bd6c10c))
* **test/gui:** mock correct modules, lazy-import GUI, and skip cleanly without Tk ([c5dd712](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/c5dd712e1f2d01c5eeb3196ce21a4716baf97354))
* **test:** access list_tables result via 'data' key for correct assertion ([7791546](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/779154693aeb3e9eaf40a51c3ea9e216b251f044))
* **test:** close DB and run gc before deleting test DB file to avoid file lock errors ([b745bad](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b745badf4df838a1154f1419c497493da21510b6))
* **test:** implement logging verification for all Data Layer modules ([0bd3c42](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0bd3c4217b5adf417b292e41cd8bba85547bc07d))
* **test:** release global DB reference and force gc before deleting test DB file in API tests ([a0127e6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a0127e617f1cb38216ee4dc7f077724efd6280a1))
* **test:** Resolve failures in GUI test suite ([c0bbf39](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/c0bbf394f118c853493617b0e8d39ca7a3e23e01))
* **transactions:** enforce admin role when is_admin=True instead of trusting the flag; keep logging and responses consistent ([2a1c27f](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/2a1c27fd69f884707b3c332151e37f5d7f5625b9))
* **transactions:** enforce delete authorization and return clear errors for not-found/unauthorized cases ([8b859cf](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8b859cf363c2368f9df171c512a6d6d480a513b7))
* **validation:** avoid treating 0 as missing with explicit presence checks; keep error messages stable ([838ec80](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/838ec8047254f894676f606f916efef967128407))
* **validation:** parameterize validation tests for expenses, contacts, and transactions ([3a4589a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/3a4589a9778b99324e29a6e2d130c096c23a148d))


### Documentation

* add high-level explanations ([97ad07a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/97ad07aea366ba5b21fa684d159c26cf4406ad8a))
* enhance README for developer branch (structure, managers responsibilities, logging & balances sections) ([fc27ddb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/fc27ddbd18cb03f8d9f70990b8c260fca9ae8356))
* **readme:** add __init__.py and __main__.py to the tree for the correct display ([5ebb746](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5ebb746bf3848c37e72fa933086251794193d765))
* **readme:** Add thread-safe API singleton, idempotent deletes, deterministic ordering, pagination/filters, balances. ([110cbe7](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/110cbe73a7c7c983b8b7e4d1d761f9fa8f635caa))
* **readme:** Refine descriptions in README.md ([6dea704](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/6dea704b5f9b2da073a2fc45b389f91d3a4edb6f))
* **readme:** update README with complete project structure, usage, and test coverage ([544eb96](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/544eb9608cb0ffef1bc5764d80379969a85ddcb1))
* **readme:** update with users/roles, auditing, pagination, deterministic listings; add admin "12345" academic policy note ([ea07441](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ea07441ae2810332211d004beea96f80dc22287b))
* update API usage and docstring for admin and role logic in api.py ([5a2aeec](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5a2aeec14453b68f6e1ac75fd8e7b47abc9fad0b))


### Performance improvements

* **database:** add index on expenses.category_id and ensure creation after optional ALTER; retain existing schema and comments ([7167878](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/71678787e102803fc8996174bebdab66ff93cdc4))


### Tests

* Add module-level docstrings to all test modules to clearly state their coverage and intent, improving readability, onboarding, and maintenance. ([ae70edb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ae70edbb9e8eff7b50507bc34a22581ae931e179))
* **api:** add admin role and visibility tests in test_api.py (preserve existing tests) ([5e3632a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5e3632a46a28aec093c7ab97390c6a1ec028212c))
* **api:** add API tests file ([1716521](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/1716521f2c6e7a713da895f824e62f6749c68dd6))
* **api:** add coverage for api_update_expense, api_update_transaction, and api_get_contact_balance ([6403e24](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/6403e24d86972374ed22f81d9e7e714978bcea35))
* **api:** add integration tests for unified API layer (expenses, contacts, transactions) ([7466fda](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7466fdac1526cba23acd858f332c9ddeab4b7074))
* **api:** add is_admin misuse guard (no leak for normal user) ([e7b193b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e7b193b1f7564d92c87d3050649357e5cbc85feb))
* **api:** cover net balance and breakdown, add api_health check, received-transactions path; harden teardown for Windows ([a24bc14](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a24bc1449b77c1deec6708d432f6567047edbc1e))
* **api:** cover NET balance and breakdown; add api_health schema_version check; harden teardown for Windows file locks ([15a7ff7](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/15a7ff718232d700c9ecab9f2cc2a59f071fea0c))
* **api:** E2E add expense with category_id and retrieve; keep admin visibility checks ([ff60028](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ff600286d08d4aa5dcd50a6e0971f56aafaa2fca))
* **api:** improve API tests with response format and error case coverage ([62f35e2](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/62f35e21aca2e91e9f93a6ea8019b4a7a6e9b36c))
* **api:** update calls to new signatures and cover admin/role and analytics paths ([cca027e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cca027e7a16b17edd65a902b23e4498dfdf53bdd))
* **api:** use set_db_path to ensure API operates on test database during testing ([a26693a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a26693a8f11600061633361f02d0243f795178f2))
* **auth:** update imports to MoneyMate.data_layer.auth ([c218ec2](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/c218ec2e8073f5cd0d2616ec74327f811fa9701b))
* **categories:** add API invalid name cases ([2a0ffc0](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/2a0ffc055d8eca3bd1f7f60d7cc9586f53db08dc))
* **categories:** add cross-user same-name and unauthorized delete cases; keep CRUD and expense validation; rely on tmp_path cleanup ([a11980d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a11980d705977a20d2b01fb26e45ca938e0b0fd8))
* **categories:** create the file test_categories.py ([ba522d5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ba522d501bcd51cd54a6ba7da33964a0fdc68f2c))
* **categories:** implementing test CRUD, ceck to the unicity of an ID and integration with expenses (validate category_id e exintance after delete) ([8b96a5b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8b96a5b8cc10920fb8141907e4769f9c357c4c4c))
* **contacts:** add docstrings and parameterize invalid name test ([f62569a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f62569adde2faecd481f2f426c916485680109a5))
* **contacts:** add gc.collect() in teardown for reliable test DB cleanup on Windows ([949b1fe](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/949b1fe708e9850d22c58114ed4e3367f8e86ead))
* **contacts:** make fixture teardown Windows-safe with retry for DB file cleanup ([023e769](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/023e769854b5ee9d6d20445167fdcd7117dbc3ed))
* **data_layer:** moved inside data_layer ([11a2d91](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/11a2d91e964eadad27bf4f83e42015881e64806d))
* **data_layer:** moved inside data_layer ([5aa8900](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5aa8900e3ad7a1cc3017c88fab7312edd1705d6d))
* **database, manager:** force gc.collect() in teardown for reliable test DB cleanup and prevent file locks ([926e51d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/926e51d55b6b55dbc4bc0ca1f6c7760f9bc6cd56))
* **database:** add docstrings and response format check for list_tables ([f8a1b52](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f8a1b52218ebaefe1c7cba825929a1514e2e45d4))
* **database:** add logic for db initialization, connection, and table listing ([b04a515](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b04a515932d95e6b2ee341abe0b09583c8aba50d))
* **database:** add tests for db for initialization, connection, and table listing ([135863f](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/135863f4133544e257b34a9856aa970804c34fb4))
* **database:** add Windows-safe teardown retry loop for DB file cleanup ([78a7346](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/78a7346cbf616ed183f097aae14b9a250a7a201f))
* **database:** assert extended tables and expenses.category_id exist ([ac06dc4](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ac06dc4091025f5d93a29d5adf9b39c2522c5d90))
* **database:** ensure users table exposes role column for RBAC in test_database.py ([3a9b541](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/3a9b541e6e054c341d42cd521cb89e04cd07f147))
* **expenses:** add docstrings and parameterize invalid expense field tests ([190ea42](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/190ea4297f0dc9279679f4a2b4777dd28590fd7c))
* **expenses:** add non-numeric price validation and category-text search filter assertions ([f80295b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f80295bfc8799ff4b0f13385b3454608c8144079))
* **expenses:** cover category_id link validation and presence in queries ([476e3a1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/476e3a135b9b25f7876fc9908e29eb46bb732fc4))
* **expenses:** ensure search returns category_id when present; make teardown Windows-safe with retry ([510de1b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/510de1b7a5cf1330b2d100eadcef2251c7578a9a))
* **expenses:** update tables_exist to expect users table in schema ([dd9517a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/dd9517a576925ad1a6da2ce4b960727296e15101))
* **gui,charts:** increase coverage, harden charts fakes, stabilize message assertions ([4a10006](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/4a1000684dcdd4a352ba25a28ec81343d726eb60))
* **gui/expenses:** extend coverage for update/search/validation and messages ([ba9760b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ba9760b4b162e38f395c6412c1c53747dbefacc5))
* **gui/login:** add tests for successful, failed and missing-field login flows ([96fb63f](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/96fb63f0b571b8ad527ad67b05a8f646302f7b3a))
* **gui/register:** add tests for registration success, short password and API error ([754b519](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/754b519eb297c17c2f30fbca4c4ac60ca5144ec1))
* **gui/transactions:** stabilize add flow (return_value) and broaden filter/search checks ([4e18c67](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/4e18c674a73ccb42d0cec9385bfce53a6153c31b))
* **logging:** accept idempotent delete 'noop' logs for expenses/contacts/transactions and keep API call checks ([8c6c2f9](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8c6c2f955e752de9de78f5e93bb5a0d14a86053d))
* **logging:** add docstrings to all log tests and clarify log assertion logic ([e8c124a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e8c124a0c13aa63a8dceb312a20507f6d6b0774c))
* **logging:** align delete-transaction log assertion with new not-found/authorization messages ([5e88b3c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/5e88b3cb80138c51299c8795c016a5f60bc75d75))
* **logging:** harden module teardown on Windows with retry; keep existing API logging coverage unchanged ([e7b035e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e7b035e0044740055d69769d5a327d6bd5d0e942))
* **logging:** harden test_logging.py and add get_logger coverage ([01426d4](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/01426d429b497500fa5fc0b43873f7d33b6e21bd))
* **manager:** add fixture and schema initialization to manager test for best practices ([ce961f3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ce961f33f1faf9dceddf7f7592a247acc541ff36))
* **manager:** add test file for DatabaseManager ([6098411](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/60984116741d39436337d8ac6f19534f4e1a4fb0))
* **manager:** add test's logic for DatabaseManager foundamental table listing ([229b545](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/229b545bc58225c7b285cdf3d869abab940f58b3))
* **manager:** add Windows-safe teardown retry loop for DB file cleanup ([8b427a7](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8b427a73e9e05287f17c3db7df507dec9d87d589))
* **manager:** assert role support and user role upgrade via DatabaseManager in test_manager.py ([b3c8944](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b3c8944b1fb0c538086213f42f4e69caf5d1cd8e))
* **manager:** use tmp_path-backed DB to avoid Windows file locks; remove manual setup/teardown and unused imports ([243602e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/243602e958076ab6c5c619a39fc0d89ee41fb956))
* migrate and refactor contact unit tests from test/unit/test_data_layer.py ([45deae0](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/45deae05f9514dcb1253c44e5268b7df997ac20c))
* migrate and refactor expense unit tests from test/unit/test_data_layer.py ([3c2c27e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/3c2c27e92b16bab185530bb78976a34156a8523f))
* migrate and refactor transaction unit tests from test/unit/test_data_layer.py ([227be4b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/227be4b72adf27128f05f73111cb3399fa943b13))
* **system:** add end-to-end API test covering users, categories, expenses, contacts, transactions and balances ([77c8ce1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/77c8ce14f3b608ad39d5a94eceb06a5cae27c546))
* **transactions:** add docstrings and parameterize invalid transaction field tests ([13333c9](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/13333c93bcfc00fe93ba856ff445a0467cc480c8))
* **transactions:** add gc.collect() in teardown to avoid file lock issues during test DB removal ([bf63956](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/bf639564d0ffd9fa50ddb7de27e78b0bc8163a95))
* **transactions:** add manager-level net balance and breakdown coverage; make teardown Windows-safe with retry ([1b94f1b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/1b94f1bb23316148558e8cbe016d89f1d8ec1ec9))
* **transactions:** add unauthorized delete by receiver and is_admin flag misuse guard for normal user ([95811e8](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/95811e8e32cbfb6442f729b450c0ebaaafdfb0a8))
* **transactions:** align receiver delete with idempotent semantics (deleted=0) and keep admin/isolation balance tests ([4412533](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/44125331519b2d9f0ded0382d6dc6ba662ec0e3e))
* **transactions:** verify admin can view all transactions and normal users can’t bypass scope in test_transactions.py ([d52203c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d52203c1a2e9b06cd97616dca88d7759e124dca8))
* update tests to align with English data layer (error messages, field names, and values) ([6ec6ced](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/6ec6ced84a981df589d100ec1d9fece767bd262c))
* **usermanager:** audit access events (login, failed_login, password_change, password_reset) via access_logs ([2365da2](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/2365da2861bd7d508b0685e5e6370b20e0776a91))
* **usermanager:** audit logout event and assert failure on wrong old password during change_password ([d2dde74](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d2dde741cd1f3d021bc39fe3d8f108fd04ef1cbb))
* **usermanager:** cover admin registration policy, role ops, and password flows in test_usermanager.py ([7b1a414](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7b1a41474854621dfedb43bc0ccd32e0c0a54719))
* **usermanager:** ensure db connection is closed for file cleanup and Windows compatibility ([8c4dd6a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8c4dd6aea5a7c2f077a99121da890e097b86a7ed))
* **usermanager:** force garbage collection and retry db file removal for Windows compatibility ([b6116b3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b6116b351159d1e8a8c40b128aac950430a43f97))
* **usermanager:** implement test logic for user registration and authentication scenarios ([38654dc](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/38654dca9741aa5c5886c47999a99adbeb1d523d))
* **usermanager:** validate invalid role assignment and role query for non-existent user ([d9cf8ca](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d9cf8cad67d960ffa304f0494945c16776db3d25))
* **validation:** add invalid transaction date format case ([0b1a138](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0b1a138d54c632671227c39d874ad50fb91c8f64))
* **validation:** add unit tests file ([094d7b9](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/094d7b9b771a7657c8afb6ad745f8531c4f340bb))
* **validation:** added logic for expense, contact, and transaction validators ([460c890](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/460c8908679b077cdb9f9ae715361cd03ee461be))
* **validation:** expand coverage with whitespace handling, numeric casting, and case-insensitive type checks ([291e274](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/291e274ac21bccae0a44e55240fe139d9646862a))


### General maintenance

* add initial moneymate.db database file to repository ([069b413](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/069b413642ef17f06a04299a0445998f9c677663))
* **categories:** create categories.py module ([713fdc1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/713fdc12685031a4f2e57a378f7e8a7212e7f689))
* **ci:** switch test runner from unittest to pytest in check.yml ([0396d5d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0396d5d448ba87c018a4ff9d4333b93600e8d2e9))
* **data_layer:** add empty init.py to enable package imports ([c3ae11f](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/c3ae11fe3fb4278334b46defe850eb0b92ab3d1a))
* **data_layer:** add UserManager and corresponding test file for user account management ([4f7c8bd](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/4f7c8bd9180dbe5590c5c1b548c41a173a30a37a))
* **data_layer:** remove duplicate set_db_path function from api.py ([9a2ea61](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9a2ea61d7e7b1dc760c6f18d32e70d61488b06f2))
* **data-layer/contacts.py:** use context manager for all DB operations to prevent file locks and ensure safe connection close ([f23bf59](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f23bf595ef9a477636a4e9926455d69bf72fdf92))
* **data-layer:** add constants and standard API response function ([ab389bb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ab389bb4880f2d9f6da9e2cf458049360c59ddc1))
* **data-layer:** move code from data_layer.py to api.py for clarity ([79c65ab](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/79c65ab96459164d26b0f6881a4f3a4d63b0bf66))
* **data-layer:** move code from data_layer.py to contacts.py for clarity ([18387b6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/18387b6d7555cd5e19eb588bcfdca4cfb93dbdc7))
* **data-layer:** move code from data_layer.py to database.py for clarity ([434beac](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/434beac43496e609520d1ed2593d227c7e0eb0ba))
* **data-layer:** move code from data_layer.py to expenses.py for clarity ([ce8483b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ce8483b2d047505dcdc0a71cf7fdf63a14c04f15))
* **data-layer:** move code from data_layer.py to transactions.py for clarity ([a6d57a5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a6d57a5d59c937f4d6a5e17867dbaa6248fe849c))
* **data-layer:** move code from data_layer.py to validation.py for clarity ([02e6f39](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/02e6f39b9da1b32df70841162bcd5d811c8507b4))
* **database:** use context manager for DB operations in init_db and list_tables for safer connection handling ([25f4cdc](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/25f4cdcd49683b6c443865a53985666804e437b3))
* **dev-deps:** add pytest>=7.0.0 to requirements-dev.txt ([8791279](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/87912799a26b201dd01c77dfe119d915a7a5d319))
* **feature/database:** rename project from my_project to MoneyMate ([e698ca9](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e698ca93a6c6e34fe1497351ec0421f6c8c48b00))
* ignore local SQLite databases and journals ([9d2c0cb](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9d2c0cbd985e5ad651a9f500611aae573e3d716e))
* **logging:** add centralized logging configuration file ([30f2dee](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/30f2deea58ba27bfcb4bfa439eaa02b33dd47d1f))
* **logging:** add centralized logging configuration for the data layer ([14c585a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/14c585a3a69f58f0d09e3da1b240d8401ff05b52))
* **logging:** make logging level configurable via MONEYMATE_LOG_LEVEL; preserve existing format and comments ([d13dfb5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d13dfb5bb4c9f01953cb9b9cd988f19ab9ab9ea7))
* **manager:** update manager.py to include UserManager and expose .users attribute ([8bb5592](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8bb55929cc86e536e4c072ca94064e89f0c1cfa6))
* **pytest:** add base pytest configuration with markers ([f444343](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f4443432ff74d528216fd9ff2e34492378cf7e3b))
* remove empty artifact directory ([1b4af3c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/1b4af3cab43087997e9e36e1267ab9c1fe966e10))
* remove empty artifact directory ([77f6afe](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/77f6afe09a736f29f46181edab0dd2ddb9976a1e))
* rename test folder from unit to data_layer ([057e53b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/057e53bf244b7445b60e76a470087b40d83611fc))
* requirements update to make python 3.9 working ([e50547d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e50547dd336e4c0768dc3496ef7172002030e07b))
* **test:** add __init__.py to test/unit for pytest discovery ([e2fdbb3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e2fdbb30eface326058a040e4f89c1bd274a9baa))
* **test:** create initial logging test file for Data Layer ([be4ee11](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/be4ee11bba2f0eaf3cdaa086c13436667960b5bb))
* **test:** trigger CI by adding a blank line to test_api.py ([1c6bc6a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/1c6bc6a153c2d4990612bf1596cf5d895f933883))
* **transactions:** use context manager for all DB operations to prevent file locks and ensure safe connection close ([cfbfd03](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cfbfd034d47c0981f16d713a155cf2212176e9d9))
* update README.md ([ff6a214](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ff6a214afe23cda777d764996fa311a71510bb93))


### Refactoring

* **api:** self-initialize via get_db and close old ([b3b2f8b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b3b2f8b6b56f504c1b6f5d2089bab70019281009))
* **api:** update API functions to use dynamic DatabaseManager instance ([b4481e2](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b4481e2890493def824060b2d883ecc6400b7ac0))
* **data_layer/expenses:** use 'with' context manager for DB connections ([7494785](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7494785b1c79ff1108e90b7c2e73f12fc25286d2))
* **data_layer:** implement structured logging in all modules ([b2dc0ec](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b2dc0ecfba485d004c4afd1f5927a603c0e84236))
* **expenses:** migrate all functions to ExpensesManager class ([9563bb3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9563bb39111f262018d27aa809120a51ab7f278a))
* **manager:** initialize/migrate DB; keeper connection for shared in-memory DB; set_db_path support ([0ade3ff](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0ade3ffd4d1436699f2f31c5e0e1569a72934eb6))
* **manager:** store db_path on the instance for diagnostics and future reuse; preserve existing behavior and comments ([08988bc](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/08988bcc7499d0783a1cd0bb943e24d365072c7e))
* remove data_layer.py and test_data_layer.py as their logic is now modularized for better usage and to respect the Single Responsibility Principle ([a5515ad](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a5515adb5b2ba19d606e79521e611a2bcda53508))
* **test_contacts:** use ContactsManager interface from DatabaseManager for all contact operations ([0ea1ed3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0ea1ed3a4b31f9e4cdcc9c05ee16cb6658b0d3d8))
* **test_expenses:** use ExpensesManager interface from DatabaseManager for all expense operations ([f576e55](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f576e55dc3f94f78eb8d3d447bcf0af2138164cf))
* **test_transactions:** use ContactsManager and TransactionsManager via DatabaseManager for all transaction and contact operations ([aa47d8f](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/aa47d8fe2cb64892e05349d57ade15b9ded8079b))
* **usermanager:** use sqlite_schema to detect access_logs table; maintain best-effort audit logging behavior ([7ec738d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7ec738dbe0810d84fc85fd99e50e37c98d0d8ca9))

## [1.0.1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/compare/1.0.0...1.0.1) (2025-10-08)


### Bug Fixes

* **CI:** add pytest to requirements-dev.txt for CI tests ([6c5733c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/6c5733c0f7470a6757d401501d3ae6fc8d344c06))
* Update PyPI authentication; now using API token for Twine authentication via PYPI_TOKEN secret. ([e48e2a3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e48e2a35340f67f8b2f10aa9768f5d305bc92406))


### Tests

* update test references from my_project to MoneyMate ([8ca4af6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8ca4af683ff9bd1c3f1a6059ad96310ccd3dd004))


### General maintenance

* **release:** 1.0.1 [skip ci] ([cff30b1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cff30b14e6bd625bbbeb6cbeb9a1df03b020c0b0))
* rename project from my_project to MoneyMate ([4aa449a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/4aa449a524e546d0a07b4a11dc5562ea03bb8f11))
* rename project from my_project to MoneyMate ([e46639b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e46639b20776ac05931a5e3738f9f607049ad2ea))
* update Python version to 3.11.9 in .python-version ([86f2e50](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/86f2e50b5ecd53f227b6e020b93c3753da8c5667))

## [1.0.1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/compare/1.0.0...1.0.1) (2025-08-25)


### Bug Fixes

* **CI:** add pytest to requirements-dev.txt for CI tests ([6c5733c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/6c5733c0f7470a6757d401501d3ae6fc8d344c06))
* Update PyPI authentication; now using API token for Twine authentication via PYPI_TOKEN secret. ([e48e2a3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e48e2a35340f67f8b2f10aa9768f5d305bc92406))


### Tests

* update test references from my_project to MoneyMate ([8ca4af6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8ca4af683ff9bd1c3f1a6059ad96310ccd3dd004))


### General maintenance

* rename project from my_project to MoneyMate ([4aa449a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/4aa449a524e546d0a07b4a11dc5562ea03bb8f11))
* rename project from my_project to MoneyMate ([e46639b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e46639b20776ac05931a5e3738f9f607049ad2ea))
* update Python version to 3.11.9 in .python-version ([86f2e50](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/86f2e50b5ecd53f227b6e020b93c3753da8c5667))

## 1.0.0 (2025-08-20)


### Features

* add renaming script ([ed33dbc](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ed33dbc03a68a605e6df7a9465c6985ec9d1e130))
* first commit ([6ddc082](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/6ddc08296facfe64fe912fcd00a255adb2806193))


### Dependency updates

* **deps:** node 18.18 ([73eec49](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/73eec49c6fc53fe3158a0b94be99dcaf6eb328eb))
* **deps:** update dependencies ([0be2f8d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0be2f8deb9b8218e509ea0926ceeb78a7a2baa70))
* **deps:** update dependency pandas to v2.1.2 ([8fe0d36](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8fe0d36a83c74ff23c059735a69f91ebef4904f3))
* **deps:** update dependency pandas to v2.1.3 ([27eb2b6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/27eb2b6e5cd7bdac497412095bdd71ee8bc9f12c))
* **deps:** update dependency pandas to v2.1.4 ([cd2b1d4](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cd2b1d4c3d22d352a89d57794402df9c8779b5c6))
* **deps:** update dependency pandas to v2.2.0 ([b8df6b1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b8df6b14bdb94a9e4d290a67ae9090227da61d29))
* **deps:** update dependency pandas to v2.2.1 ([be273ce](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/be273ce0d591432389c5da7d8bee343079db4871))
* **deps:** update dependency scikit-learn to v1.3.2 ([fe7eea2](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/fe7eea22d078a77ed77477a78785c387953888f8))
* **deps:** update dependency scikit-learn to v1.4.0 ([85de0ed](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/85de0ed24d38277ea86a7ac71781631c097e8aaf))
* **deps:** update dependency scikit-learn to v1.4.1.post1 ([d24ef8b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d24ef8bc4bedf055630f95eb04a6db1833b3d4d7))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.69 ([fa07343](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/fa07343c199db9cf3a0784abdf1858983f80392c))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.70 ([2f7eb9b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/2f7eb9b20f5fc44a154c18cdf4ddb413da9819fc))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.71 ([e7efd4f](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/e7efd4f39ac7396621ae9a7182c42975d8756476))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.72 ([17cd38c](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/17cd38c5f6969e7be37be61087c63047d462e00a))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.73 ([ceba297](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ceba297fb66930fa41cfcc36794f37b16d041c60))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.74 ([a7c030d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/a7c030de41394700cc0cec89358e59a3709377b2))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.75 ([21e6b9a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/21e6b9af441d069af6c13ccbd55bad63d4a9a841))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.76 ([fcf51ce](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/fcf51ce4d1048739ca4933ef56cefe69b1f25bb9))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.77 ([24c1ad5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/24c1ad5c7c2a6df6f8519c4bd3bfd9892cac7bdd))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.78 ([4881854](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/488185409ad1263b83838fba5b07136517c9fe52))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.79 ([b09d25f](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b09d25f30d81f9bc22cee76f3cf2fe72e1589e62))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.80 ([d9e55c5](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d9e55c51fa21cf880450cbeee619cca167e55cec))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.81 ([d2608f8](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d2608f87dc1bb2554c4db8bd8fe57fb75512efdb))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.82 ([22b0719](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/22b0719f19296441890e9e6f122df45efd5e095e))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.83 ([8f2ec20](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/8f2ec20935428b99b28d412040689e56fa30a07e))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.84 ([cb92e70](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/cb92e703568dbf402c51434c510fd97cb6946c52))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.85 ([f05865d](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f05865d98e638d8c7192bfdb360898b7152400f9))
* **deps:** update node.js to 20.10 ([f393b2a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f393b2a2fb2d3aa98b5c5a969ef4df442d5c79de))
* **deps:** update node.js to 20.11 ([63410da](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/63410da68d5122d155caac39b6f99de19d619825))
* **deps:** update node.js to 20.9 ([d107ca2](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d107ca20dd8414ef39ab6b6b95740b3ae2c75f16))
* **deps:** update node.js to v20 ([61b7e25](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/61b7e250a9afe02465f435c6b709b2fcc872e338))
* **deps:** update python docker tag to v3.11.6 ([199ffe6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/199ffe6a498c6b26d358d97ac2ef7046da68e268))
* **deps:** update python docker tag to v3.12.0 ([b123d48](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b123d4847e25cc94e86faf1f5ec37a4e0b54e46d))
* **deps:** update python docker tag to v3.12.1 ([ac01a01](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/ac01a014b54008d5c7af4916880413ba864f9a33))


### Bug Fixes

* readme ([f12fb0b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/f12fb0b17c08a18a7e145199234dc38d43fd0ddb))
* release workflow ([9c84ec1](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9c84ec1497a1f8c6c438a248107746df0fa7c612))
* **release:** include .python-version in MANIFEST.in ([9d794fa](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/9d794faac19b032c5a0f149c3e5e44df018db17b))
* renovate configuration ([0db8978](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0db89788ad8bef935fa97b77e7fa05aca749da28))
* **workflow:** grant write permissions to contents for deploy workflow call ([530cee7](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/530cee7de0b1b26b53069559482089562b38cec4))


### Tests

* adding tests for data layer (DTT) in tests/ ([21a77b7](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/21a77b706994d3747c80c63aced7339e73e6eea3))


### Build and continuous integration

* **deps:** update actions/setup-node action to v4 ([45c9acd](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/45c9acdfed764240e4e150e65a4507205537a16a))
* **deps:** update actions/setup-python action to v5 ([66921e3](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/66921e3580f3223689adf1665a323befbd9b3272))
* enable semantic release ([648759b](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/648759ba41fda0cad343493709a57bcb908f7229))
* fix release by installing correct version of node ([d809f17](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d809f17fc96c7295e0ec526161a56f558d49aa47))


### General maintenance

* **ci:** dry run release on testpypi for template project ([b90a25a](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/b90a25a0f1f439e0bf548eec0bfae21b1f8c44b1))
* **ci:** update deploy workflow to use GH_TOKEN and set correct permissions ([d2ac514](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d2ac514d63d021f2595ae83082a0c40f9a5e86ca))
* **ci:** use jq to parse package.json ([66af494](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/66af494bc406d4b9b649153f910016cceb1b63ce))
* initial todo-list ([154e024](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/154e024ac1bb8a1f1c99826ab2ed6a28e703a513))
* **release:** 1.0.0 [skip ci] ([d3b0c79](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/d3b0c791fdf4d93194e560c1f6a6cc40736a34d8))
* **release:** 1.0.1 [skip ci] ([903a69e](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/903a69e21c365754ca9d83e8d2797e1ceb602757))
* **release:** simplify renovate conf ([23da9b6](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/23da9b61d38adbe974c53240f05fb71ea685fb03))
* remove useless Dockerfile ([0272af7](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/0272af71647e254f7622d38ace6000f0cbc7f17d))
* write some instructions ([7da9554](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact/commit/7da9554a6e458c5fc253a222b295fbeb6a7862ec))

## [1.0.1](https://github.com/aequitas-aod/template-python-project/compare/1.0.0...1.0.1) (2024-02-02)


### Dependency updates

* **deps:** update dependency pandas to v2.1.2 ([8fe0d36](https://github.com/aequitas-aod/template-python-project/commit/8fe0d36a83c74ff23c059735a69f91ebef4904f3))
* **deps:** update dependency pandas to v2.1.3 ([27eb2b6](https://github.com/aequitas-aod/template-python-project/commit/27eb2b6e5cd7bdac497412095bdd71ee8bc9f12c))
* **deps:** update dependency pandas to v2.1.4 ([cd2b1d4](https://github.com/aequitas-aod/template-python-project/commit/cd2b1d4c3d22d352a89d57794402df9c8779b5c6))
* **deps:** update dependency pandas to v2.2.0 ([b8df6b1](https://github.com/aequitas-aod/template-python-project/commit/b8df6b14bdb94a9e4d290a67ae9090227da61d29))
* **deps:** update dependency scikit-learn to v1.3.2 ([fe7eea2](https://github.com/aequitas-aod/template-python-project/commit/fe7eea22d078a77ed77477a78785c387953888f8))
* **deps:** update dependency scikit-learn to v1.4.0 ([85de0ed](https://github.com/aequitas-aod/template-python-project/commit/85de0ed24d38277ea86a7ac71781631c097e8aaf))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.69 ([fa07343](https://github.com/aequitas-aod/template-python-project/commit/fa07343c199db9cf3a0784abdf1858983f80392c))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.70 ([2f7eb9b](https://github.com/aequitas-aod/template-python-project/commit/2f7eb9b20f5fc44a154c18cdf4ddb413da9819fc))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.71 ([e7efd4f](https://github.com/aequitas-aod/template-python-project/commit/e7efd4f39ac7396621ae9a7182c42975d8756476))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.72 ([17cd38c](https://github.com/aequitas-aod/template-python-project/commit/17cd38c5f6969e7be37be61087c63047d462e00a))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.73 ([ceba297](https://github.com/aequitas-aod/template-python-project/commit/ceba297fb66930fa41cfcc36794f37b16d041c60))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.74 ([a7c030d](https://github.com/aequitas-aod/template-python-project/commit/a7c030de41394700cc0cec89358e59a3709377b2))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.75 ([21e6b9a](https://github.com/aequitas-aod/template-python-project/commit/21e6b9af441d069af6c13ccbd55bad63d4a9a841))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.76 ([fcf51ce](https://github.com/aequitas-aod/template-python-project/commit/fcf51ce4d1048739ca4933ef56cefe69b1f25bb9))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.77 ([24c1ad5](https://github.com/aequitas-aod/template-python-project/commit/24c1ad5c7c2a6df6f8519c4bd3bfd9892cac7bdd))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.78 ([4881854](https://github.com/aequitas-aod/template-python-project/commit/488185409ad1263b83838fba5b07136517c9fe52))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.79 ([b09d25f](https://github.com/aequitas-aod/template-python-project/commit/b09d25f30d81f9bc22cee76f3cf2fe72e1589e62))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.80 ([d9e55c5](https://github.com/aequitas-aod/template-python-project/commit/d9e55c51fa21cf880450cbeee619cca167e55cec))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.81 ([d2608f8](https://github.com/aequitas-aod/template-python-project/commit/d2608f87dc1bb2554c4db8bd8fe57fb75512efdb))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.82 ([22b0719](https://github.com/aequitas-aod/template-python-project/commit/22b0719f19296441890e9e6f122df45efd5e095e))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.83 ([8f2ec20](https://github.com/aequitas-aod/template-python-project/commit/8f2ec20935428b99b28d412040689e56fa30a07e))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.84 ([cb92e70](https://github.com/aequitas-aod/template-python-project/commit/cb92e703568dbf402c51434c510fd97cb6946c52))
* **deps:** update dependency semantic-release-preconfigured-conventional-commits to v1.1.85 ([f05865d](https://github.com/aequitas-aod/template-python-project/commit/f05865d98e638d8c7192bfdb360898b7152400f9))
* **deps:** update node.js to 20.10 ([f393b2a](https://github.com/aequitas-aod/template-python-project/commit/f393b2a2fb2d3aa98b5c5a969ef4df442d5c79de))
* **deps:** update node.js to 20.11 ([63410da](https://github.com/aequitas-aod/template-python-project/commit/63410da68d5122d155caac39b6f99de19d619825))
* **deps:** update node.js to 20.9 ([d107ca2](https://github.com/aequitas-aod/template-python-project/commit/d107ca20dd8414ef39ab6b6b95740b3ae2c75f16))
* **deps:** update node.js to v20 ([61b7e25](https://github.com/aequitas-aod/template-python-project/commit/61b7e250a9afe02465f435c6b709b2fcc872e338))
* **deps:** update python docker tag to v3.12.0 ([b123d48](https://github.com/aequitas-aod/template-python-project/commit/b123d4847e25cc94e86faf1f5ec37a4e0b54e46d))
* **deps:** update python docker tag to v3.12.1 ([ac01a01](https://github.com/aequitas-aod/template-python-project/commit/ac01a014b54008d5c7af4916880413ba864f9a33))


### Bug Fixes

* **release:** include .python-version in MANIFEST.in ([9d794fa](https://github.com/aequitas-aod/template-python-project/commit/9d794faac19b032c5a0f149c3e5e44df018db17b))


### Build and continuous integration

* **deps:** update actions/setup-node action to v4 ([45c9acd](https://github.com/aequitas-aod/template-python-project/commit/45c9acdfed764240e4e150e65a4507205537a16a))
* **deps:** update actions/setup-python action to v5 ([66921e3](https://github.com/aequitas-aod/template-python-project/commit/66921e3580f3223689adf1665a323befbd9b3272))

## 1.0.0 (2023-10-12)


### Features

* add renaming script ([ed33dbc](https://github.com/aequitas-aod/template-python-project/commit/ed33dbc03a68a605e6df7a9465c6985ec9d1e130))
* first commit ([6ddc082](https://github.com/aequitas-aod/template-python-project/commit/6ddc08296facfe64fe912fcd00a255adb2806193))


### Dependency updates

* **deps:** node 18.18 ([73eec49](https://github.com/aequitas-aod/template-python-project/commit/73eec49c6fc53fe3158a0b94be99dcaf6eb328eb))
* **deps:** update dependencies ([0be2f8d](https://github.com/aequitas-aod/template-python-project/commit/0be2f8deb9b8218e509ea0926ceeb78a7a2baa70))
* **deps:** update python docker tag to v3.11.6 ([199ffe6](https://github.com/aequitas-aod/template-python-project/commit/199ffe6a498c6b26d358d97ac2ef7046da68e268))


### Bug Fixes

* readme ([f12fb0b](https://github.com/aequitas-aod/template-python-project/commit/f12fb0b17c08a18a7e145199234dc38d43fd0ddb))
* release workflow ([9c84ec1](https://github.com/aequitas-aod/template-python-project/commit/9c84ec1497a1f8c6c438a248107746df0fa7c612))
* renovate configuration ([0db8978](https://github.com/aequitas-aod/template-python-project/commit/0db89788ad8bef935fa97b77e7fa05aca749da28))


### Build and continuous integration

* enable semantic release ([648759b](https://github.com/aequitas-aod/template-python-project/commit/648759ba41fda0cad343493709a57bcb908f7229))
* fix release by installing correct version of node ([d809f17](https://github.com/aequitas-aod/template-python-project/commit/d809f17fc96c7295e0ec526161a56f558d49aa47))


### General maintenance

* **ci:** dry run release on testpypi for template project ([b90a25a](https://github.com/aequitas-aod/template-python-project/commit/b90a25a0f1f439e0bf548eec0bfae21b1f8c44b1))
* **ci:** use jq to parse package.json ([66af494](https://github.com/aequitas-aod/template-python-project/commit/66af494bc406d4b9b649153f910016cceb1b63ce))
* initial todo-list ([154e024](https://github.com/aequitas-aod/template-python-project/commit/154e024ac1bb8a1f1c99826ab2ed6a28e703a513))
* remove useless Dockerfile ([0272af7](https://github.com/aequitas-aod/template-python-project/commit/0272af71647e254f7622d38ace6000f0cbc7f17d))
* write some instructions ([7da9554](https://github.com/aequitas-aod/template-python-project/commit/7da9554a6e458c5fc253a222b295fbeb6a7862ec))
