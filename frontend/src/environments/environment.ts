export const environment = {
  production: false,

  // OPCIÓN 1: Backend LOCAL
  apiUrl: 'http://localhost:5000/api',

  // OPCIÓN 2: Backend REMOTO (Entorno de desarrollo compartido)
  // apiUrl: 'https://devapps.emergiacc.com/SipoApiRest/api',

  apiUrlAutenticacion: 'https://devapps.emergiacc.com/ApiRestAutenticacion/api/Login/Authenticate',
  activeDirectoryKey: 'ea1a29308c7b4385bcdf019fe198d646',
  apiUrlGetDomains: 'https://devapps.emergiacc.com/ApiRestActiveDirectory/api/ActiveDirectory/GetDomainsActiveDirectoryFromJsonUpdatedAsync',
  apiUrlLoginActiveDirectory: 'https://devapps.emergiacc.com/ApiRestActiveDirectory/api/ActiveDirectory/AuntenticateByUserActiveDirectoryAsync'
};