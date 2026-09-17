import type { AdapterEndpoint } from 'odin-react';
import type { FurnaceEndpointTypes } from '../../EndpointTypes';

import { Col, Row, Form, FloatingLabel } from 'react-bootstrap';
import { TitleCard, WithEndpoint, EndpointButton } from 'odin-react';
import { floatingInputStyle } from '../../utils';

const EndPointFormControl = WithEndpoint(Form.Control);

interface PidOverrideProps {
    furnaceEndPoint: AdapterEndpoint<FurnaceEndpointTypes>;
    connectedDisable: boolean;
    title: string;
    pid: "pid_upper" | "pid_lower";
}

function PidOverride(props: PidOverrideProps) {
    const {furnaceEndPoint} = props;
    const {connectedDisable} = props;
    const {title} = props;
    const {pid} = props;

    return (
      <TitleCard
        title={
          <Row>
            <Col xs={6} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>{title}</Col>
            <Col xs={3}>
              <EndpointButton
                endpoint={furnaceEndPoint}
                fullpath={pid+"/override/enable"}
                variant={furnaceEndPoint.data?.[pid]?.override?.enable ? 'danger' : 'primary'}
                value={furnaceEndPoint.data?.[pid]?.override?.enable ? false : true}
                >
                  {furnaceEndPoint.data?.[pid]?.override?.enable ? "Disable" : "Enable"}
              </EndpointButton>
            </Col>
          </Row>
        }>
        <Col>
          <FloatingLabel
              label="Output %">
              <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  fullpath={pid+"/override/percent_out"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
              />
          </FloatingLabel>
        </Col>
      </TitleCard>
    )
}

export default PidOverride;