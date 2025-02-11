const DEF_API_VERSION = '0.1';

class AdapterEndpoint 
{
    constructor(adapter, api_version=DEF_API_VERSION) 
    {
        this.adapter = adapter;
        this.api_version = api_version;
    }

    build_url(path)
    {
        return `api/${this.api_version}/${this.adapter}/${path}`;
    }

    async get(path='') 
    {
        const url = this.build_url(path);
        const response = await fetch(
            url,
            { 
                method: 'GET',
                headers: {'Accept': 'application/json'}
            }
        );

        if (!response.ok) {
            var message;
            try {
                const err_result = await response.json();
                message = err_result.error;
            }
            catch
            {
                message = `GET request to ${url} failed with status ${response.status}`;  
            }
            throw new Error(message);
        }
        const result = await response.json();
        return result;
    }

    async put(data, path='')
    {
        const url = this.build_url(path);
        const response = await fetch(
            url,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data)
            }
        );

        if (!response.ok) {
            var message;
            try {
                const err_result = await response.json();
                message = err_result.error;
            }
            catch
            {
                message = `PUT request to ${url} failed with status ${response.status}`;
            }
            throw new Error(message);
        }
        const result = await response.json();
        return result;
    }

}