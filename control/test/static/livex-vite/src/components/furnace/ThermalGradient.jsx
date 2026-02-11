import React from 'react';

import { checkNull } from '../../utils';

import { TitleCard, WithEndpoint } from 'odin-react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

import { floatingInputStyle, floatingLabelStyle } from '../../utils';
import { FloatingLabel } from 'react-bootstrap';

const EndpointSelect = WithEndpoint(Form.Select);
const EndPointButton = WithEndpoint(Button);
const EndPointFormControl = WithEndpoint(Form.Control);

function ThermalGradient(props){
    const {furnaceEndPoint} = props;
    const {connectedDisable} = props;

    const high_metadata = furnaceEndPoint.metadata.gradient?.high_heater;

    return (
      <TitleCard title={
        <Row>
          <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Thermal Gradient</Col>
          <Col xs={3}>
            <EndPointButton
              endpoint={furnaceEndPoint}
              fullpath="gradient/enable"
              value={furnaceEndPoint.data?.gradient?.enable ? false : true}
              variant={furnaceEndPoint.data?.gradient?.enable ? 'danger' : 'primary'}
              >
                {furnaceEndPoint.data?.gradient?.enable ? "Disable" : "Enable"}
            </EndPointButton>
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
                buttonText={furnaceEndPoint.data.gradient?.high_heater}
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
                  value={checkNull(furnaceEndPoint.data.gradient?.actual)}
                />
            </FloatingLabel>
            <FloatingLabel
              label="Theoretical">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data.gradient?.theoretical)}
                />
            </FloatingLabel>
          </Col>
        </Row>
      </TitleCard>
    )
}

export default ThermalGradient;
