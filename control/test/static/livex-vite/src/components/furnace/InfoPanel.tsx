import type { AdapterEndpoint } from 'odin-react';
import type { FurnaceEndpointTypes } from '../../EndpointTypes';

import { Col, Row, InputGroup } from 'react-bootstrap';
import { TitleCard } from 'odin-react';
import { checkNull, usePrevious } from '../../utils';

interface InfoPanelProps {
    furnaceEndPoint: AdapterEndpoint<FurnaceEndpointTypes>;
}

function InfoPanel(props: InfoPanelProps) {
    const {furnaceEndPoint} = props;

    const lastInput_upper = usePrevious(furnaceEndPoint.data?.pid_upper?.temperature);
    const lastInput_lower= usePrevious(furnaceEndPoint.data?.pid_lower?.temperature);

    // Fixing the label width of the display labels so that they're consistent
    // ~6px per character.
    const labelWidth = 80;
    const valueWidth = 65;

    const labelStyling = {
        width: valueWidth,
        border: '1px solid lightblue',
        backgroundColor: '#e0f7ff'
      }

  // Predo calcs for typing in calculation reasons
  // Calcs must be done with defined values. So if any aren't defined, whole thing is for checkNull
  const upperPid = furnaceEndPoint.data?.pid_upper;

  const upperPlcVolt =
    upperPid?.output != null &&
    upperPid?.output_scalar != null
      ? upperPid.output * 0.1 * upperPid.output_scalar
      : undefined;

  const upperPGain =
    upperPid?.proportional != null &&
    upperPid?.setpoint != null &&
    upperPid?.temperature != null
      ? upperPid.proportional * (upperPid.setpoint - upperPid.temperature)
      : undefined;

  const upperISumDiff =
    upperPid?.integral != null &&
    upperPid?.setpoint != null &&
    upperPid?.temperature != null
      ? upperPid.integral * (upperPid.setpoint - upperPid.temperature)
      : undefined;

  const upperDSumDiff =
    upperPid?.derivative != null &&
    upperPid?.temperature != null &&
    lastInput_upper != null
      ? upperPid.derivative * (upperPid.temperature - lastInput_upper)
      : undefined;

  const lowerPid = furnaceEndPoint.data?.pid_lower;

  const lowerPlcVolt =
    lowerPid?.output != null &&
    lowerPid?.output_scalar != null
      ? lowerPid.output * 0.1 * lowerPid.output_scalar
      : undefined;

  const lowerPGain =
    lowerPid?.proportional != null &&
    lowerPid?.setpoint != null &&
    lowerPid?.temperature != null
      ? lowerPid.proportional * (lowerPid.setpoint - lowerPid.temperature)
      : undefined;

  const lowerISumDiff =
    lowerPid?.integral != null &&
    lowerPid?.setpoint != null &&
    lowerPid?.temperature != null
      ? lowerPid.integral * (lowerPid.setpoint - lowerPid.temperature)
      : undefined;

  const lowerDSumDiff =
    lowerPid?.derivative != null &&
    lowerPid?.temperature != null &&
    lastInput_lower != null
      ? lowerPid.derivative * (lowerPid.temperature - lastInput_lower)
      : undefined;

  return (
    <TitleCard title={
      <Row>
        <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Monitor Panel</Col>
      </Row>
    }>
      <Row>
        <label>Extra Thermocouples</label>
        <Col xs={4} md={6} xl={4}>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.value)}
              </InputGroup.Text>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.value)}
                </InputGroup.Text>
          </InputGroup>
        </Col>
        <Col xs={4} md={6} xl={4}>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.value)}
                </InputGroup.Text>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.value)}
                </InputGroup.Text>
          </InputGroup>
        </Col>
      </Row>
      <Row className="mt-3">
        <Col xs={6} xl={4}>
          <label>Upper PID</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Out
              </InputGroup.Text>
              <InputGroup.Text
                style={labelStyling}>
                  {checkNull(furnaceEndPoint.data?.pid_upper?.output)}
              </InputGroup.Text>
            </InputGroup>
            </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  PLC Volt.
                </InputGroup.Text>
                <InputGroup.Text
                  style={labelStyling}>
                    {checkNull(upperPlcVolt)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
          <Row className="mt-3">
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                P Gain
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(upperPGain)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                I Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(upperDSumDiff)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                D Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(upperISumDiff)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Out Sum
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(furnaceEndPoint.data?.pid_upper?.outputsum)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
        </Col>
        <Col xs={6} xl={4}>
          <label>Lower PID</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Out
              </InputGroup.Text>
              <InputGroup.Text
                style={labelStyling}>
                  {checkNull(furnaceEndPoint.data?.pid_lower?.output)}
              </InputGroup.Text>
            </InputGroup>
            </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  PLC Volt.
                </InputGroup.Text>
                <InputGroup.Text
                  style={labelStyling}>
                    {checkNull(lowerPlcVolt)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
          <Row className="mt-3">
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                P Gain
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(lowerPGain)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                I Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(lowerISumDiff)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                D Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(lowerDSumDiff)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Out Sum
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(furnaceEndPoint.data?.pid_lower?.outputsum)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
        </Col>
      </Row>
    </TitleCard>
  )
}


export default InfoPanel