import Row from 'react-bootstrap/Row';
import { useAdapterEndpoint } from 'odin-react';
import InferenceCard from './cameras/InferenceCard';


function InferencePage(props) {
    const { endpoint_url } = props;

    const cameraEndPoint = useAdapterEndpoint('camera', endpoint_url, 1000);

    // Destructuring data and cameras safely
    const cameras = cameraEndPoint?.data || {} // Fallback to an empty object if no data

    return (
      <Row>
        {Object.keys(cameras).map((key) => (
          <InferenceCard
            key={key}
            endpoint_url={endpoint_url}
            name={cameraEndPoint.data[key].camera_name}
          />
        ))}
      </Row>
    )
}

export default InferencePage;