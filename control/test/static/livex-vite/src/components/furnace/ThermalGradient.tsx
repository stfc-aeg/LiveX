import type { AdapterEndpoint } from 'odin-react';
import type { FurnaceEndpointTypes } from '../../EndpointTypes';

import { TitleCard, WithEndpoint, EndpointButton } from 'odin-react';
import { Row, Col, Form, FloatingLabel } from 'react-bootstrap';
import { checkNull, floatingInputStyle, floatingLabelStyle } from '../../utils';

const EndpointSelect = WithEndpoint(Form.Select);
const EndPointFormControl = WithEndpoint(Form.Control);

interface ThermalGradientProps {
    furnaceEndPoint: AdapterEndpoint<FurnaceEndpointTypes>;
    connectedDisable: boolean;
}

function ThermalGradient(props: ThermalGradientProps){
    const {furnaceEndPoint, connectedDisable} = props;

    const high_metadata = furnaceEndPoint.metadata?.gradient?.high_heater;

    return (
      <TitleCard title={
        <Row>
          <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Thermal Gradient</Col>
          <Col xs={3}>
            <EndpointButton
              endpoint={furnaceEndPoint}
              fullpath="gradient/enable"
              value={furnaceEndPoint.data?.gradient?.enable ? false : true}
              variant={furnaceEndPoint.data?.gradient?.enable ? 'danger' : 'primary'}
              >
                {furnaceEndPoint.data?.gradient?.enable ? "Disable" : "Enable"}
            </EndpointButton>
          </Col>
        </Row>
      }>

        <Row>
          <Col xs={6}>
            <FloatingLabel
              label="K/mm">
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  type="number"
                  fullpath="gradient/wanted"
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            <FloatingLabel
              label="Space (mm)">
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  type="number"
                  fullpath="gradient/distance"
                  event_type="enter"
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
            </FloatingLabel>
            <FloatingLabel
              label="Gradient high towards heater:">
              <EndpointSelect
                endpoint={furnaceEndPoint}
                fullpath="gradient/high_heater"
                variant="outline-secondary"
                buttonText={furnaceEndPoint.data?.gradient?.high_heater}
                disabled={connectedDisable}
                style={floatingInputStyle}>
                  {(high_metadata?.allowed_values ?? []).map(
                    (selection, index) => (
                      <option value={selection} key={index}>{selection}</option>
                    )
                  )}
              </EndpointSelect>
            </FloatingLabel>
          </Col>
          <Col xs={6}>
            <FloatingLabel
              label="Actual">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data?.gradient?.actual)}
                />
            </FloatingLabel>
            <FloatingLabel
              label="Theoretical">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data?.gradient?.theoretical)}
                />
            </FloatingLabel>
          </Col>
        </Row>
      </TitleCard>
    )
}

export default ThermalGradient;
