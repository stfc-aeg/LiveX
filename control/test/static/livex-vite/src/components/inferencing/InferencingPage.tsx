import type { InferencingEndpointTypes } from '../../EndpointTypes';

import Row from 'react-bootstrap/Row';
import { useAdapterEndpoint } from '@dssg/odin-react';
import InferencingCard from './InferencingCard';

interface InferencePageProps {
  endpoint_url: string;
}

function InferencePage(props: InferencePageProps) {
    const { endpoint_url } = props;

    const inferencingEndpoint = useAdapterEndpoint<InferencingEndpointTypes>('inferencing', endpoint_url, 1000);

    // Destructuring data and cameras safely
    const endpoints = inferencingEndpoint?.data?.endpoint || {} // Fallback to an empty object if no data

    return (
      <Row>
        {Object.keys(endpoints).map((key) => (
          <InferencingCard
            key={key}
            endpoint={inferencingEndpoint}
            endpoint_url={endpoint_url}
            name={inferencingEndpoint?.data?.endpoint?.[key]?.endpoint_name || 'Unknown Endpoint'}
          />
        ))}
      </Row>
    )
}

export default InferencePage;