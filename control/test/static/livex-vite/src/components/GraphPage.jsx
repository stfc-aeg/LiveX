import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { useAdapterEndpoint } from 'odin-react';
import MonitorGraph from './furnace/MonitorGraph';


function GraphPage(props) {
    const { endpoint_url } = props;
    const graphEndPoint = useAdapterEndpoint('graph', endpoint_url, 200);

    return (
      <Row>
        <Col xs={12} sm={12} lg={12} xl={6} xxl={6}>
        <MonitorGraph
          endpoint={graphEndPoint}
          paths={[
          'temperature_upper/data',
          'temperature_lower/data',
          'setpoint_upper/data',
          'setpoint_lower/data',
          ]}
          seriesNames={['TC_Upper', 'TC_Lower', 'SP_Upper', 'SP_Lower']}
          title={"Temperature and Setpoint Graph"}
        ></MonitorGraph>
        </Col>
        <Col xs={12} sm={12} xl={6} xxl={6}>
        <MonitorGraph
          endpoint={graphEndPoint}
          paths={['output_upper/data', 'output_lower/data']}
          seriesNames={['PO_Upper','PO_Lower']}
          title={"PID Output Graph"}
        ></MonitorGraph>
        </Col>
      </Row>
    )
}

export default GraphPage;